#!/usr/bin/env python3
"""LLMs as recognizers on the CLARA grid benchmarks (HenryKautz/CLARA).

Same problems, evidence, goals and scoring as CLARA's max-term, SharpSAT-TD and
MC-SAT runs, so the LLMs can be compared with them file by file.

Subcommands:
  prompt   print the prompt for one evidence file
  check    offline checks: counts, true goals, prompt contents, scoring replay
  run      query models; raw responses go to results/clara/raw/<model>.jsonl
  score    accuracy and P(true) beside the recognizers; writes report.md + CSVs

Task sets (--set):
  pilot    8 problems across the families, 96 evidence files
  all      every problem with a recognition file, 1,088 evidence files
  simple   SimpleGrid 3x3-7x7, 160 evidence files, for the plain prompt

Prompt variants (--variant):
  same     states the clock and the final-slice rule, as the recognizers assume
  plain    leaves both out

Model specs are bench.py's. Stdlib only apart from hf: models.
"""

import argparse
import concurrent.futures as cf
import csv
import json
import math
import random
import re
import sys
import threading
import time
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import bench

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "clara"
RESULTS = ROOT / "results" / "clara"

FAMILIES = ["SimpleGrid", "TwoPackage", "TwoPackageOneway", "ThreePackage", "FourPackage"]
RECOGNIZERS = ["max-term", "sharpsat-td", "mc-sat"]
LEVELS = [25, 100]  # evidence levels with a true goal; 0 is the no-evidence file
RUN_LIMIT = 1800    # seconds per call, CLARA's limit per recognition run

EXPECTED_FILES = {"SimpleGrid": 352, "TwoPackage": 160, "TwoPackageOneway": 160,
                  "ThreePackage": 80, "FourPackage": 336}
PILOT = {("SimpleGrid", "grid3x3-1"), ("SimpleGrid", "grid6x6-1"), ("SimpleGrid", "grid10x10-1"),
         ("TwoPackage", "grid3x3-1"), ("TwoPackage", "grid7x7-1"), ("TwoPackageOneway", "grid3x3-1"),
         ("ThreePackage", "grid5x5-1"), ("FourPackage", "grid6x6-1")}

# USD per 1M input / output tokens, standard tier, from
# developers.openai.com/api/docs/pricing on 2026-11-05.
PRICES = {"gpt-6-luna": (0.10, 0.50), "gpt-5.4-mini": (0.75, 4.50),
          "gpt-6.1-sol": (2.00, 10.00), "gpt-5.5": (5.00, 30.00)}

HYP_LINE = re.compile(r"^;;\s+(\S+)\s+(\(.*\))\s+shortest horizon (\d+)\s*$", re.M)
RECOGNITION_HORIZON = re.compile(r"Recognition horizon: (\d+)")
TRUE_GOAL = re.compile(r"True hypothesis: (\S+?)\.")
OCCURS = re.compile(r"\(occurs\s+(\([^()]*\))\s+(\d+)\)")
PROBLEM_NAME = re.compile(r"^(grid(\d+)x\d+-\d+)-")


# ---------------------------------------------------------------- instances

def squeeze(form):
    return " ".join(form.split())


def top_level_forms(text):
    forms, depth, start = [], 0, None
    for i, c in enumerate(text):
        if c == "(":
            if depth == 0:
                start = i
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                forms.append(text[start:i + 1])
    return forms


def find_form(text, head):
    """(start, end) of the balanced form that opens with `head`."""
    start = text.index(head)
    depth = 0
    for i in range(start, len(text)):
        depth += (text[i] == "(") - (text[i] == ")")
        if depth == 0:
            return start, i + 1
    raise ValueError(f"unbalanced {head}")


def goal_disjuncts(goal_form):
    """The disjuncts of (:goal (or ...)), allowing a one-child (and ...) around it."""
    body = top_level_forms(goal_form[len("(:goal"):-1])[0]
    while squeeze(body).startswith("(and ") and len(top_level_forms(body[1:-1])) == 1:
        body = top_level_forms(body[1:-1])[0]
    if not squeeze(body).startswith("(or "):
        raise ValueError(f"goal is not a disjunction: {squeeze(body)[:80]}")
    return [squeeze(f) for f in top_level_forms(body[1:-1])]


def load_problem(family, name):
    raw = (DATA / family / "recognition" / f"{name}.pddl").read_text()
    hyps = {n: squeeze(f) for n, f, _ in HYP_LINE.findall(raw)}
    text = bench.strip_comments(raw)
    start, end = find_form(text, "(:goal")
    if sorted(goal_disjuncts(text[start:end])) != sorted(hyps.values()):
        raise ValueError(f"{family}/{name}: header and goal list different hypotheses")
    # The candidates are listed separately in the prompt, in shuffled order.
    without_goal = "\n".join(l for l in (text[:start] + text[end:]).splitlines() if l.strip())
    return {"family": family, "name": name, "hyps": hyps, "problem_pddl": without_goal,
            "horizon": int(RECOGNITION_HORIZON.search(raw).group(1))}


def evidence_level(filename):
    if filename.endswith("-none.txt"):
        return 0
    return int(re.search(r"-obs(\d+)\.txt$", filename).group(1))


def load_tasks():
    """Every evidence file of every problem with a recognition file."""
    tasks = []
    for family in FAMILIES:
        problems = {p.stem: load_problem(family, p.stem) for p in sorted((DATA / family / "recognition").glob("*.pddl"))}
        for path in sorted((DATA / family / "evidence").glob("*.txt")):
            m = PROBLEM_NAME.match(path.name)
            raw = path.read_text()
            true = TRUE_GOAL.search(raw)
            obs = [(int(t), squeeze(a)) for a, t in OCCURS.findall(bench.strip_comments(raw))]
            tasks.append({"family": family, "problem": m.group(1), "size": int(m.group(2)),
                          "evidence": f"{family}/evidence/{path.name}", "pct": evidence_level(path.name),
                          "true": true.group(1) if true else None, "obs": obs,
                          "instance": problems[m.group(1)]})
    return tasks


def select_tasks(name, levels):
    tasks = [t for t in load_tasks() if t["pct"] in levels]
    if name == "pilot":
        tasks = [t for t in tasks if (t["family"], t["problem"]) in PILOT]
    elif name == "simple":
        tasks = [t for t in tasks if t["family"] == "SimpleGrid" and t["size"] <= 7]
    return tasks


def goal_labels(task, variant, sample):
    """{label: goal name}, in listing order. Shuffled per file, variant and sample,
    so no model sees a fixed order and every model sees the same one."""
    names = sorted(task["instance"]["hyps"])
    random.Random(repr((task["evidence"], variant, sample))).shuffle(names)
    return {f"hyp{i}": n for i, n in enumerate(names)}


DOMAIN_PDDL = None


def domain_pddl():
    global DOMAIN_PDDL
    if DOMAIN_PDDL is None:
        DOMAIN_PDDL = bench.strip_comments((DATA / "clara-logistics.pddl").read_text())
    return DOMAIN_PDDL


def agent_rules(variant, steps):
    costs = "Action costs are given in the problem, and the agent tends to prefer low-cost plans."
    prior = "All candidate goals are equally likely beforehand."
    if variant == "plain":
        return ["The agent's plan achieves its goal.", costs, prior]
    return [f"The agent acts for {steps} time steps. In each step it performs one or more "
            "non-conflicting actions, or none.",
            "Its goal counts as achieved only if it is true after the final time step.",
            costs, prior]


def observation_rules(variant):
    rules = ["Each observed action is listed with its time step.", "Steps not listed were not observed."]
    if variant == "plain":
        rules.append("The agent may have acted further after the last observed step.")
    return rules


def observed_lines(task):
    return [f"step {t}: {a}" for t, a in task["obs"]]


def build_prompt(task, labels, variant):
    inst = task["instance"]
    steps = inst["horizon"] - 1
    bullets = lambda rules: "\n".join(f"- {r}" for r in rules)
    goals = "\n".join(f"{lab}: {inst['hyps'][name]}" for lab, name in labels.items())
    observed = "\n".join(observed_lines(task)) or "(none)"
    first, last = next(iter(labels)), list(labels)[-1]
    return f"""Goal recognition task.

An agent acts in the planning domain below, starting from the given initial state. Its goal is exactly one of the candidate goals listed, but you do not know which. You observe some of its actions.

About the agent:
{bullets(agent_rules(variant, steps))}

About the observations:
{bullets(observation_rules(variant))}

## Domain (PDDL)
{domain_pddl()}

## Problem: objects and initial state (PDDL)
{inst['problem_pddl']}

## Candidate goals
{goals}

## Observed actions
{observed}

## What to return
Estimate the posterior probability of each candidate goal given the observations. Respond with a JSON object of this form:
{{
  "reasoning": "<brief explanation>",
  "probabilities": {{"hyp0": <number>, "hyp1": <number>, ...}},
  "most_likely": "<label of the single most likely goal>"
}}
Include every label from {first} to {last} in "probabilities". The probabilities must be non-negative and sum to 1."""


# ---------------------------------------------------------------- models

def with_limit(fn, args):
    """bench.with_retries, except that all attempts share CLARA's per-run limit."""
    deadline = time.time() + args.limit
    delay = 2.0
    for attempt in range(args.retries + 1):
        left = deadline - time.time()
        if left <= 0:
            raise bench.ApiError("run limit reached", retryable=False)
        try:
            return fn(argparse.Namespace(**{**vars(args), "timeout": left}))
        except bench.ApiError as e:
            if not e.retryable or attempt == args.retries:
                raise
            time.sleep(min(delay + random.random(), max(deadline - time.time(), 0)))
            delay = min(delay * 2, 60)


def call_jev(spec, task, labels, variant, args):
    """Jev's Choice primitive, with the candidate goals as its options. The answer
    is stored in the same JSON shape the chat models return."""
    inst = task["instance"]
    rules = agent_rules(variant, inst["horizon"] - 1) + observation_rules(variant)
    instructions = ("An agent acts in the planning domain `domain_pddl`, starting from the objects and initial "
                    "state in `problem_pddl`. Its goal is exactly one of the options, but you do not know which. "
                    "`observed_actions` lists some of its actions. " + " ".join(rules) +
                    " Which option is the agent's goal?")
    resp = with_limit(lambda a: bench.jev_request(
        spec,
        {"domain_pddl": domain_pddl(), "problem_pddl": inst["problem_pddl"], "observed_actions": observed_lines(task)},
        {"goal": {"type": "choice", "instructions": instructions,
                  "criteria": {lab: f"The agent's goal is {inst['hyps'][name]}" for lab, name in labels.items()}}},
        a), args)
    ans = resp["answers"]["goal"]
    usage = resp.get("usage") or {}
    content = json.dumps({"reasoning": None, "probabilities": ans["probabilities"],
                          "most_likely": ans["choice"], "confidence": ans.get("confidence")})
    return {"content": content, "finish_reason": "stop", "served_model": resp.get("model"),
            "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
            "reasoning_tokens": None}


def call_hf(spec, user, seed, args):
    """bench.call_hf, with the reply limit cut to what the model's context leaves."""
    import nextaction  # lazy: pulls in torch/transformers only when an hf: model is used
    with nextaction._hf_lock:
        model = nextaction.hf_model(spec, args)
        used = len(model.encode(model.render(bench.SYSTEM_PROMPT, user)))
        room = args.max_tokens or 2048
        context = getattr(model.model.config, "max_position_embeddings", None)
        if context:
            room = min(room, context - used)
        if room < 1:
            raise bench.ApiError(f"prompt of {used} tokens leaves no room in a context of {context}", retryable=False)
        out = model.generate(bench.SYSTEM_PROMPT, user, args.temperature, room, seed)
    out.update(served_model=spec[3:], max_new_tokens=room,
               finish_reason="length" if out["output_tokens"] >= room else "stop")
    return out


def call_model(spec, task, labels, variant, sample, args):
    seed = zlib.crc32(repr((spec, task["evidence"], variant, sample)).encode())
    if bench.is_jev(spec):
        return call_jev(spec, task, labels, variant, args)
    user = build_prompt(task, labels, variant)
    if spec.startswith("mock-"):
        return bench.call_mock(spec, list(labels), seed)
    if spec.startswith("hf:"):
        return call_hf(spec, user, seed, args)
    return with_limit(lambda a: bench.call_openai(spec, bench.SYSTEM_PROMPT, user, a), args)


def is_priced(spec):
    return not (spec.startswith(("mock-", "hf:")) or bench.is_jev(spec))


def call_cost(rec):
    price = PRICES.get(bench.parse_spec(rec["model"])[0])
    if not price:
        return 0.0
    return ((rec.get("input_tokens") or 0) * price[0] + (rec.get("output_tokens") or 0) * price[1]) / 1e6


# ---------------------------------------------------------------- run

def raw_path(results, spec, variant):
    # One file per model and prompt: appends from jobs on different nodes clobber each other on Ceph.
    suffix = "" if variant == "same" else f".{variant}"
    return Path(results) / "raw" / (re.sub(r"[^\w.@-]+", "_", spec) + suffix + ".jsonl")


def read_raw(results):
    records = []
    for path in sorted((Path(results) / "raw").glob("*.jsonl")):
        with path.open() as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    # A killed job can leave half a line; skipping it makes a rerun redo that call.
                    print(f"skipping unreadable line {n} of {path}", file=sys.stderr)
    return records


def record_key(r):
    return (r["model"], r["variant"], r["evidence"], r["sample"])


def cmd_run(args):
    for spec in args.model:
        if is_priced(spec) and bench.parse_spec(spec)[0] not in PRICES:
            sys.exit(f"{spec} has no price in PRICES, so the spending cap could not cover it")
    (Path(args.results) / "raw").mkdir(parents=True, exist_ok=True)
    records = read_raw(args.results)
    # A timeout is a result, as in CLARA's records; API errors are retried on a rerun.
    done = {record_key(r) for r in records if r["status"] in ("ok", "timeout")}
    tasks = select_tasks(args.set, args.levels)
    jobs = [(spec, task, s) for spec in args.model for task in tasks for s in range(args.samples)
            if (spec, args.variant, task["evidence"], s) not in done]
    print(f"{len(jobs)} calls to make ({len(tasks)} evidence files, {args.samples} samples, variant {args.variant})")
    if args.dry_run:
        print(Counter(j[0] for j in jobs))
        return
    msg = bench.missing_keys({j[0] for j in jobs})
    if msg:
        sys.exit(msg)

    lock = threading.Lock()
    stop = threading.Event()
    spent = [sum(call_cost(r) for r in records)]
    print(f"spent so far: ${spent[0]:.2f} of ${args.max_usd:.2f}")

    def work(job):
        spec, task, s = job
        if stop.is_set():
            return None
        if is_priced(spec) and spent[0] >= args.max_usd:
            stop.set()
            return None
        labels = goal_labels(task, args.variant, s)
        rec = {"model": spec, "variant": args.variant, "family": task["family"], "problem": task["problem"],
               "size": task["size"], "evidence": task["evidence"], "pct": task["pct"], "sample": s,
               "true_goal": task["true"], "labels": labels, "time": time.time()}
        t0 = time.time()
        try:
            rec.update(call_model(spec, task, labels, args.variant, s, args))
            rec.update(status="ok", error=None)
        except (bench.ApiError, KeyError, ValueError, RuntimeError, TypeError) as e:
            rec.update(status="timeout" if time.time() - t0 >= args.limit else "error", error=str(e))
        rec["latency_s"] = round(time.time() - t0, 3)
        with lock:
            with raw_path(args.results, spec, args.variant).open("a") as f:
                f.write(json.dumps(rec) + "\n")
            spent[0] += call_cost(rec)
        return rec

    failed = in_a_row = finished = 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for fut in cf.as_completed([ex.submit(work, j) for j in jobs]):
            rec = fut.result()
            if rec is None:
                continue
            finished += 1
            bad = rec["status"] != "ok"
            failed += bad
            in_a_row = in_a_row + 1 if bad else 0
            note = f"{rec['status'].upper()} {rec['error'][:120]}" if bad else "ok"
            print(f"[{finished}/{len(jobs)}] {rec['model']} {rec['evidence']} s={rec['sample']} "
                  f"{rec['latency_s']:.1f}s ${spent[0]:.2f} {note}", flush=True)
            if in_a_row >= args.max_errors_in_a_row and not stop.is_set():
                print(f"stopping: {in_a_row} failures in a row", flush=True)
                stop.set()
    if spent[0] >= args.max_usd:
        print(f"stopped at the spending cap: ${spent[0]:.2f} of ${args.max_usd:.2f}")
    print(f"finished {finished} of {len(jobs)} calls; {failed} failed; spent ${spent[0]:.2f}")


# ---------------------------------------------------------------- scoring

def score_answer(dist, true):
    """CLARA's rule on values rounded as in its records: 1/k when the true goal is
    among k goals tied for the highest probability, else 0."""
    rounded = {g: round(p, 4) for g, p in dist.items()}
    top = max(rounded.values())
    ties = [g for g, p in rounded.items() if p == top]
    return (1 / len(ties) if true in ties else 0.0), rounded[true]


def llm_rows(records):
    latest = {}
    for r in records:  # a later record supersedes, except that a failure never replaces an answer
        key = record_key(r)
        if r["status"] != "ok" and key in latest and latest[key]["status"] == "ok":
            continue
        latest[key] = r
    rows = []
    for r in latest.values():
        row = {k: r.get(k) for k in ("model", "variant", "family", "problem", "size", "evidence", "pct", "sample",
                                     "status", "finish_reason", "input_tokens", "output_tokens",
                                     "reasoning_tokens", "latency_s", "max_new_tokens")}
        row.update(valid=False, chance=1 / len(r["labels"]), cost_usd=call_cost(r))
        if r["status"] == "ok" and r.get("pct"):
            dist, _ = bench.parse_answer(r.get("content"), list(r["labels"]))
            if dist:
                by_goal = {r["labels"][lab]: p for lab, p in dist.items()}
                score, p_true = score_answer(by_goal, r["true_goal"])
                row.update(valid=True, score=score, p_true=p_true)
        rows.append(row)
    return rows


def recognizer_rows(tasks):
    """CLARA's recorded runs on the same files, through the same scorer."""
    by_file = {t["evidence"]: t for t in tasks}
    rows = []
    for family in FAMILIES:
        latest = {}
        with (DATA / family / "results" / "runs.jsonl").open() as f:
            for line in f:
                r = json.loads(line)
                latest[(r["evidence"], r["method"])] = r  # the last record counts
        for (evidence, method), r in latest.items():
            task = by_file.get(f"{family}/{evidence}")
            if not task:
                continue
            row = {"model": method, "variant": "recognizer", "family": family, "problem": task["problem"],
                   "size": task["size"], "evidence": task["evidence"], "pct": task["pct"], "sample": 0,
                   "status": r["status"], "latency_s": r.get("wall_s"), "valid": False,
                   "chance": 1 / len(task["instance"]["hyps"]), "recorded_score": r.get("score"),
                   "recorded_true": r.get("true_goal")}
            if r["status"] == "ok":
                score, p_true = score_answer(r["posterior"], task["true"])
                row.update(valid=True, score=score, p_true=p_true)
            rows.append(row)
    return rows


def state_after(task):
    """{object: place} once the observed actions have run from the initial state."""
    start, end = find_form(task["instance"]["problem_pddl"], "(:init")
    at = dict(re.findall(r"\(at ([^\s()]+) ([^\s()]+)\)", task["instance"]["problem_pddl"][start:end]))
    for _, action in task["obs"]:
        name, *params = action.strip("()").split()
        if name in ("drive", "fly"):
            at[params[0]] = params[2]
        elif name == "load":
            at.pop(params[0], None)
        elif name == "unload":
            at[params[0]] = params[2]
        else:
            raise ValueError(f"unknown action {action}")
    return at


def stop_rule(task):
    """Baseline: spread the probability over the goals already true when the
    observations stop, or over all goals if none is. Every plan ends as soon as
    its goal holds, so with the whole plan observed this always finds the truth."""
    at = state_after(task)
    hyps = task["instance"]["hyps"]
    true_now = [n for n, f in hyps.items()
                if all(at.get(o) == p for o, p in re.findall(r"\(at ([^\s()]+) ([^\s()]+)\)", f))]
    pool = true_now or list(hyps)
    return {n: (1 / len(pool) if n in pool else 0.0) for n in hyps}


def baseline_rows(tasks):
    rows = []
    for t in tasks:
        score, p_true = score_answer(stop_rule(t), t["true"])
        rows.append({"model": "stop-rule", "variant": "baseline", "family": t["family"], "problem": t["problem"],
                     "size": t["size"], "evidence": t["evidence"], "pct": t["pct"], "sample": 0, "status": "ok",
                     "valid": True, "score": score, "p_true": p_true, "chance": 1 / len(t["instance"]["hyps"])})
    return rows


def file_means(rows):
    """{evidence file: (accuracy, P(true))}, averaging a file's valid samples."""
    by_file = defaultdict(list)
    for r in rows:
        if r["valid"]:
            by_file[r["evidence"]].append(r)
    return {e: (bench.mean(x["score"] for x in rs), bench.mean(x["p_true"] for x in rs))
            for e, rs in by_file.items()}


def bootstrap_ci(diffs_by_problem, n=2000):
    """95% interval for a mean difference, resampling problems, since a problem's
    evidence files are not independent."""
    rng = random.Random(0)
    keys = list(diffs_by_problem)
    stats = []
    for _ in range(n):
        vals = []
        for _ in keys:
            vals += diffs_by_problem[rng.choice(keys)]
        stats.append(sum(vals) / len(vals))
    stats.sort()
    return stats[int(0.025 * n)], stats[int(0.975 * n)]


def paired(a_rows, b_rows):
    """[files, then for accuracy and P(true): a mean, b mean, a - b with 95% interval], on files
    both answered; None when they share no file."""
    a, b = file_means(a_rows), file_means(b_rows)
    common = sorted(a.keys() & b.keys())
    if not common:
        return None
    problem_of = {r["evidence"]: (r["family"], r["problem"]) for r in a_rows}
    cells = [len(common)]
    for i in (0, 1):
        diffs = defaultdict(list)
        for e in common:
            diffs[problem_of[e]].append(a[e][i] - b[e][i])
        lo, hi = bootstrap_ci(diffs)
        cells += [bench.fmt(bench.mean(a[e][i] for e in common), 3), bench.fmt(bench.mean(b[e][i] for e in common), 3),
                  f"{bench.mean(v for vs in diffs.values() for v in vs):+.3f} [{lo:+.3f}, {hi:+.3f}]"]
    return cells


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    return lines + ["| " + " | ".join(str(c) for c in row) + " |" for row in rows] + [""]


def size_label(size):
    return f"{size}x{size}"


def level_label(pct):
    return f"{pct}%"


def summary_rows(rows, tasks, keys):
    """One row per group: files answered of those planned, accuracy, P(true), chance."""
    planned = Counter()
    for t in tasks:
        planned[tuple(t.get(k) for k in keys if k != "model")] += 1
    groups = defaultdict(list)
    for r in rows:
        groups[tuple(r[k] for k in keys)].append(r)
    out = []
    for key, rs in groups.items():
        means = file_means(rs)
        chances = {r["evidence"]: r["chance"] for r in rs}
        plan_key = tuple(v for k, v in zip(keys, key) if k != "model")
        out.append({**dict(zip(keys, key)), "files_answered": len(means), "files_planned": planned[plan_key],
                    "accuracy": bench.mean(a for a, _ in means.values()),
                    "p_true": bench.mean(p for _, p in means.values()),
                    "chance": bench.mean(chances[e] for e in means)})
    return out


def cmd_score(args):
    results = Path(args.results)
    all_tasks = load_tasks()
    tasks = [t for t in all_tasks if t["pct"] in LEVELS]
    tasks_for_rows = [{"family": t["family"], "size": t["size"], "pct": t["pct"]} for t in tasks]
    rows = llm_rows(read_raw(results))
    llm = [r for r in rows if r["pct"] in LEVELS]
    same = [r for r in llm if r["variant"] == "same"]
    plain = [r for r in llm if r["variant"] == "plain"]
    recs = recognizer_rows(tasks) + baseline_rows(tasks)
    references = RECOGNIZERS + ["stop-rule"]
    models = sorted({r["model"] for r in rows})
    method_order = {m: i for i, m in enumerate(models + references)}

    L = ["# LLMs as recognizers on the CLARA grid benchmarks\n"]
    L.append("Data: HenryKautz/CLARA at the commit in `data/clara/SOURCE_COMMIT.txt`. **Accuracy** scores a run 1/k when "
             "the true goal is among k goals tied for the highest probability, else 0. **P(true)** is the probability "
             "given to the true goal. Both are means over answered files, averaging a file's valid samples, and "
             "methods answered different files, so compare them in the same-file table. **Chance** is 1 / number of "
             "goals. Recognizer rows come from CLARA's own run records. **stop-rule** is a baseline that needs no model: "
             "it spreads the probability over the goals already true when the observations stop. Every plan ends as "
             "soon as its goal holds, so it scores 1.0 with the whole plan; at 25% no goal is true yet, so it scores "
             "chance.\n")

    L.append("## Models\n")
    out = []
    for m in models:
        rs = [r for r in rows if r["model"] == m and r["pct"] in LEVELS]
        statuses = Counter(r["status"] for r in rs)
        ok = [r for r in rs if r["status"] == "ok"]
        out.append((m, len(rs), statuses["ok"], statuses["error"], statuses["timeout"],
                    sum(r["valid"] for r in rs), bench.fmt(sum(r["valid"] for r in rs) / len(rs) if rs else None),
                    sum(r.get("finish_reason") == "length" for r in ok),
                    bench.fmt(bench.mean(r["input_tokens"] for r in ok), 0),
                    bench.fmt(bench.mean(r["output_tokens"] for r in ok), 0),
                    bench.fmt(bench.mean(r["reasoning_tokens"] for r in ok), 0),
                    bench.fmt(bench.mean(r["latency_s"] for r in ok), 1),
                    f"${sum(r['cost_usd'] for r in rs):.2f}"))
    L += table(["model", "calls", "returned", "errors", "timeouts", "valid", "valid rate", "cut off", "in tok",
                "out tok", "reason tok", "latency s", "cost"], out)

    def summary_table(title, keys, source):
        L.append(f"## {title}\n")
        s = summary_rows(source, tasks_for_rows, keys)
        s.sort(key=lambda r: (FAMILIES.index(r["family"]), r.get("size", 0), r["pct"], method_order.get(r["model"], 99)))
        heads, cells = [], []
        for k, head in (("family", "family"), ("size", "size"), ("pct", "evidence"), ("model", "method")):
            if k in keys:
                heads.append(head)
                cells.append(k)
        out = []
        for r in s:
            row = [size_label(r[k]) if k == "size" else level_label(r[k]) if k == "pct" else r[k] for k in cells]
            out.append(row + [f"{r['files_answered']}/{r['files_planned']}", bench.fmt(r["accuracy"], 3),
                              bench.fmt(r["p_true"], 3), bench.fmt(r["chance"], 3)])
        L.extend(table(heads + ["files", "accuracy", "P(true)", "chance"], out))
        return s

    summary = summary_table("By family and evidence", ("family", "pct", "model"), same + recs)
    summary_table("By size", ("family", "size", "pct", "model"), same + recs)

    L.append("## Same-file comparison with the recognizers and the stop rule\n")
    L.append("LLM minus reference, on files both answered. Intervals are 95%, from resampling problems.\n")
    out = []
    llm_models = sorted({r["model"] for r in same})
    for m in llm_models:
        for rec in references:
            for family in FAMILIES:
                for pct in LEVELS:
                    pick = lambda src, name: [r for r in src if r["model"] == name and r["family"] == family and r["pct"] == pct]
                    cells = paired(pick(same, m), pick(recs, rec))
                    if cells:
                        out.append((m, rec, family, level_label(pct), *cells))
    L += table(["LLM", "reference", "family", "evidence", "files", "LLM acc", "ref acc", "acc diff",
                "LLM P(true)", "ref P(true)", "P(true) diff"], out)

    if plain:
        L.append("## Same prompt against plain prompt\n")
        L.append("Same files. The plain prompt leaves out the clock and the final-slice rule. Differences are plain "
                 "minus same, with 95% intervals from resampling problems.\n")
        out = []
        for m in sorted({r["model"] for r in plain}):
            for pct in LEVELS:
                cells = paired([r for r in plain if r["model"] == m and r["pct"] == pct],
                               [r for r in same if r["model"] == m and r["pct"] == pct])
                if cells:
                    out.append((m, level_label(pct), *cells))
        L += table(["model", "evidence", "files", "plain acc", "same acc", "acc diff",
                    "plain P(true)", "same P(true)", "P(true) diff"], out)

    bad = [r for r in llm if not r["valid"]]
    if bad:
        L.append("## Failed answers\n")
        counts = Counter((r["model"], r["variant"], r["status"], r.get("finish_reason")) for r in bad)
        L += table(["model", "variant", "status", "finish reason", "calls"],
                   [(*k, n) for k, n in sorted(counts.items(), key=lambda kv: str(kv[0]))])

    results.mkdir(parents=True, exist_ok=True)
    (results / "report.md").write_text("\n".join(L))
    fields = ["model", "variant", "family", "problem", "size", "evidence", "pct", "sample", "status", "valid",
              "score", "p_true", "chance", "finish_reason", "input_tokens", "output_tokens", "reasoning_tokens",
              "latency_s", "cost_usd"]
    with (results / "per_response.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fields, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["model"], r["variant"], r["evidence"], r["sample"])):
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    with (results / "summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, ["family", "pct", "model", "files_answered", "files_planned", "accuracy", "p_true", "chance"])
        w.writeheader()
        for r in summary:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print("\n".join(L))
    print(f"\nwrote {results / 'report.md'}, summary.csv, per_response.csv")


# ---------------------------------------------------------------- checks

def check_tables(recs, problems):
    """Replaying CLARA's records through score_answer must give its tables.md."""
    rows = re.compile(r"^\| (\d+)x\d+ \| (25|100)% \| (\S+) \| \d+/\d+ \| [^|]+ \| [^|]+ \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|$", re.M)
    compared = 0
    for family in FAMILIES:
        text = (DATA / family / "tables.md").read_text()
        for size, pct, method, acc, p_true, chance in rows.findall(text):
            rs = [r for r in recs if r["family"] == family and r["size"] == int(size)
                  and r["pct"] == int(pct) and r["model"] == method and r["valid"]]
            if not rs:
                problems.append(f"{family} {size}x{size} {pct}% {method}: in tables.md, not replayed")
                continue
            compared += 1
            mine = (bench.mean(r["score"] for r in rs), bench.mean(r["p_true"] for r in rs), bench.mean(r["chance"] for r in rs))
            for got, want, name in zip(mine, (acc, p_true, chance), ("accuracy", "P(true)", "chance")):
                if abs(got - float(want)) > 0.00051:
                    problems.append(f"{family} {size}x{size} {pct}% {method} {name}: replay {got:.4f}, tables.md {want}")
    return compared


def cmd_check(args):
    problems = []
    tasks = load_tasks()
    scored = [t for t in tasks if t["pct"] in LEVELS]

    counts = Counter(t["family"] for t in scored)
    if dict(counts) != EXPECTED_FILES:
        problems.append(f"evidence counts {dict(counts)}, expected {EXPECTED_FILES}")
    for name, want in (("pilot", 96), ("all", 1088), ("simple", 160)):
        got = len(select_tasks(name, LEVELS))
        if got != want:
            problems.append(f"set {name}: {got} files, expected {want}")
    print(f"evidence files with a true goal: {len(scored)} {dict(counts)}; no-evidence files: {len(tasks) - len(scored)}")

    # True goals and evidence.
    by_problem = defaultdict(dict)
    for t in tasks:
        if t["pct"] == 0:
            if t["obs"] or t["true"]:
                problems.append(f"{t['evidence']}: a no-evidence file with content")
            continue
        if t["true"] not in t["instance"]["hyps"]:
            problems.append(f"{t['evidence']}: true goal {t['true']} is not a hypothesis")
        if not t["obs"]:
            problems.append(f"{t['evidence']}: no observed actions")
        if t["obs"] and t["obs"][-1][0] > t["instance"]["horizon"] - 1:
            problems.append(f"{t['evidence']}: an action after the final time step")
        by_problem[(t["evidence"].rsplit("-obs", 1)[0])][t["pct"]] = t
    for stem, pair in by_problem.items():
        if set(pair) != {25, 100}:
            problems.append(f"{stem}: evidence levels {sorted(pair)}")
            continue
        full, part = pair[100]["obs"], pair[25]["obs"]
        if len(part) != math.ceil(len(full) * 0.25) or full[:len(part)] != part:
            problems.append(f"{stem}: the 25% file is not the first quarter of the 100% file")
        # The whole plan must reach its goal; replaying it is also a check of state_after.
        if stop_rule(pair[100])[pair[100]["true"]] == 0:
            problems.append(f"{stem}: the true goal is not reached when the whole plan has run")
    early = sum(1 for t in tasks if t["pct"] == 25 and len(set(stop_rule(t).values())) > 1)
    print(f"25% files where some goal is already true when the observations stop: {early}")

    # What the prompts contain.
    forbidden = [";;", "True hypothesis", "shortest horizon", "Recognition horizon", "(:goal", "obs25", "obs100",
                 "plan-goals", "rechyp", "at-truck", "at-pkg", "EvalMaxSAT", "tt-open-wbo"]
    first_slot_true = Counter()
    n_prompts = 0
    for t in scored:
        forms = t["instance"]["hyps"]
        for variant in ("same", "plain"):
            for s in range(3):
                labels = goal_labels(t, variant, s)
                prompt = build_prompt(t, labels, variant)
                n_prompts += 1
                for word in forbidden + [t["evidence"], Path(t["evidence"]).name]:
                    if word in prompt:
                        problems.append(f"{t['evidence']} {variant}: prompt contains {word!r}")
                listing = prompt.split("## Candidate goals\n", 1)[1].split("\n\n## Observed actions", 1)[0]
                if sorted(l.split(": ", 1)[1] for l in listing.splitlines()) != sorted(forms.values()):
                    problems.append(f"{t['evidence']} {variant}: candidate list is wrong")
                observed = prompt.split("## Observed actions\n", 1)[1].split("\n\n## What to return", 1)[0]
                if observed.splitlines() != observed_lines(t):
                    problems.append(f"{t['evidence']} {variant}: observed actions are wrong")
                has_clock = "after the final time step" in prompt and f"acts for {t['instance']['horizon'] - 1} time steps" in prompt
                if has_clock != (variant == "same"):
                    problems.append(f"{t['evidence']} {variant}: clock wording is wrong")
                if prompt != build_prompt(t, goal_labels(t, variant, s), variant):
                    problems.append(f"{t['evidence']} {variant}: prompt is not reproducible")
                first_slot_true[list(labels.values()).index(t["true"]) == 0] += 1
    share = first_slot_true[True] / sum(first_slot_true.values())
    expected = bench.mean(1 / len(t["instance"]["hyps"]) for t in scored)
    print(f"prompts checked: {n_prompts}; true goal listed first in {share:.3f} of them (expected about {expected:.3f})")
    if abs(share - expected) > 0.02:
        problems.append(f"true goal is listed first in {share:.3f} of prompts, expected about {expected:.3f}")

    # Scoring against CLARA's records and tables.
    recs = recognizer_rows(scored)
    disagree = [r for r in recs if r["valid"] and abs(r["score"] - r["recorded_score"]) > 1e-9]
    wrong_true = [r for r in recs if r.get("recorded_true") and r["recorded_true"] != next(
        t["true"] for t in by_problem[r["evidence"].rsplit("-obs", 1)[0]].values())]
    print(f"recognizer records replayed: {sum(r['valid'] for r in recs)}; score differs from the record on {len(disagree)}; "
          f"true goal differs on {len(wrong_true)}")
    for r in disagree[:10]:
        problems.append(f"{r['evidence']} {r['model']}: replay score {r['score']:.3f}, recorded {r['recorded_score']:.3f}")
    for r in wrong_true[:10]:
        problems.append(f"{r['evidence']}: recorded true goal {r['recorded_true']} differs from the evidence file")
    print(f"tables.md rows compared: {check_tables(recs, problems)}")

    if problems:
        print(f"\n{len(problems)} PROBLEMS:")
        print("\n".join(problems[:40]))
        sys.exit(1)
    print("\nall checks passed")


def cmd_prompt(args):
    task = next((t for t in load_tasks() if t["evidence"] == args.evidence), None)
    if not task:
        sys.exit(f"no evidence file {args.evidence}; expected for example "
                 "SimpleGrid/evidence/grid4x4-1-truck1-p3-4-obs25.txt")
    print(build_prompt(task, goal_labels(task, args.variant, args.sample), args.variant))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prompt", help="print one prompt")
    p.add_argument("evidence", help="for example SimpleGrid/evidence/grid4x4-1-truck1-p3-4-obs25.txt")
    p.add_argument("--variant", choices=["same", "plain"], default="same")
    p.add_argument("--sample", type=int, default=0)
    p.set_defaults(fn=cmd_prompt)

    p = sub.add_parser("check", help="offline checks; makes no model calls")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("run", help="query models")
    p.add_argument("--model", action="append", required=True, help="repeatable; bench.py's model specs")
    p.add_argument("--set", choices=["pilot", "all", "simple"], default="pilot")
    p.add_argument("--levels", nargs="+", type=int, choices=[0, 25, 100], default=LEVELS)
    p.add_argument("--variant", choices=["same", "plain"], default="same")
    p.add_argument("--samples", type=int, default=1, help="repeats per evidence file")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--max-usd", type=float, default=50.0, help="spending cap across all priced models and runs")
    p.add_argument("--max-errors-in-a-row", type=int, default=20)
    p.add_argument("--limit", type=float, default=RUN_LIMIT, help="seconds per call, retries included")
    p.add_argument("--retries", type=int, default=5)
    p.add_argument("--temperature", type=float, default=None,
                   help="OpenAI: omit for reasoning models, which reject it; hf: sampling defaults to 1.0")
    p.add_argument("--max-tokens", type=int, default=None,
                   help="OpenAI max_completion_tokens; hf max_new_tokens (default 2048, less if the context requires)")
    p.add_argument("--device", default=None, help="hf: cuda / mps / cpu (default: best available)")
    p.add_argument("--dtype", default=None, help="hf: float16 / bfloat16 / float32")
    p.add_argument("--no-chat", action="store_true", help="hf: plain-text prompt instead of the chat template")
    p.add_argument("--results", default=str(RESULTS))
    p.add_argument("--dry-run", action="store_true", help="count the calls without making them")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("score", help="compute metrics and write the report")
    p.add_argument("--results", default=str(RESULTS))
    p.set_defaults(fn=cmd_score)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
