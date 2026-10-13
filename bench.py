#!/usr/bin/env python3
"""LLM plan-recognition benchmark on the FiFO / Ramirez & Geffner instances.

Subcommands:
  prompt       print the prompt for one instance
  list-models  list the model ids your OpenAI key can use
  run          query models and append raw responses to results/raw.jsonl
  score        compute metrics and write results/report.md + CSVs

Model specs:
  <openai id>[@effort]  OpenAI chat completions (OPENAI_API_KEY)
  jev-<version>         TypeSafe's Jev (e.g. jev-latest, jev-1.13.0) through
                        its Choice primitive (TYPESAFE_API_KEY)
  hf:<repo-or-path>     a local transformers model, e.g. hf:Qwen/Qwen2.5-7B-Instruct
                        or hf:meta-llama/Meta-Llama-3-8B-Instruct (needs torch +
                        transformers; the backend lives in nextaction.py)
  mock-uniform / mock-random / mock-garbage   offline stand-ins

Stdlib only apart from hf: models. API keys are read from the environment
(never stored).
"""

import argparse
import concurrent.futures as cf
import csv
import json
import math
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
RAW = RESULTS / "raw.jsonl"

DOMAINS = {"blockwords": "BlockWords", "intrusion": "IntrusionDetection"}
EVIDENCE_LEVELS = [1, 2, 3, 4, 5]
REFERENCE_LEVELS = [1, 3, 5]  # levels with FiFO R&G / MAP results

ATOM = re.compile(r"\([^()]*\)")


# ---------------------------------------------------------------- instances

def strip_comments(text):
    lines = [l.split(";", 1)[0].rstrip() for l in text.splitlines()]
    return "\n".join(l for l in lines if l.strip())


def norm_atoms(line):
    return [" ".join(a.lower().split()) for a in ATOM.findall(line)]


def load_domain(name):
    d = DATA / name
    hyps = [norm_atoms(l) for l in (d / "hyps.dat").read_text().splitlines() if l.strip()]
    real = norm_atoms((d / "real_hyp.dat").read_text())
    true_idx = next(i for i, h in enumerate(hyps) if h == real)
    template = (d / "template.pddl").read_text().strip().lower().replace("<hypothesis>", "<HYPOTHESIS>")
    problem = template.replace("<HYPOTHESIS>", ";; hidden: one of the candidate goals below")
    return {
        "name": name,
        "domain_pddl": strip_comments((d / "domain.pddl").read_text()),
        "problem_pddl": problem,
        "hyps": hyps,
        "labels": [f"hyp{i}" for i in range(len(hyps))],
        "true": f"hyp{true_idx}",
    }


def load_evidence(name, k):
    text = strip_comments((DATA / name / f"evidence-{k}.txt").read_text())
    body = text.replace("(occur-in-order", "", 1)
    return [" ".join(a.lower().split()) for a in ATOM.findall(body)]


def load_reference(name, k):
    ref = {}
    p = DATA / name / "reference" / f"rg-evidence-{k}.tsv"
    if p.exists():
        with p.open() as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        ref["rg"] = normalize({r["hyp"]: float(r["posterior"]) for r in rows})
    p = DATA / name / "reference" / "map-summary.tsv"
    with p.open() as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if int(r["evidence_obs"]) == k:
                ref["map"] = r["recognized_hyp"].lower()
    return ref


SYSTEM_PROMPT = (
    "You are an expert in automated planning and goal recognition. "
    "Answer with a single JSON object and nothing else."
)


def build_prompt(dom, obs):
    goals = "\n".join(f"{lab}: (and {' '.join(h)})" for lab, h in zip(dom["labels"], dom["hyps"]))
    observed = "\n".join(f"{i + 1}. {a}" for i, a in enumerate(obs))
    return f"""Goal recognition task.

An agent acts in the planning domain below, starting from the given initial state. Its goal is exactly one of the candidate goals listed, but you do not know which. You observe some of its actions.

About the observations:
- They are listed in the order the agent performed them.
- The observation is partial: the agent may have performed other, unobserved actions before, between, or after the observed ones.
- The agent's full plan achieves its goal. Every action costs 1, and the agent tends to pursue its goal with low-cost (efficient) plans.

## Domain (PDDL)
{dom['domain_pddl']}

## Problem: objects and initial state (PDDL)
{dom['problem_pddl']}

## Candidate goals
{goals}

## Observed actions (in order)
{observed}

## What to return
Estimate the posterior probability of each candidate goal given the observations. Respond with a JSON object of this form:
{{
  "reasoning": "<brief explanation>",
  "probabilities": {{"hyp0": <number>, "hyp1": <number>, ...}},
  "most_likely": "<label of the single most likely goal>"
}}
Include every label from {dom['labels'][0]} to {dom['labels'][-1]} in "probabilities". The probabilities must be non-negative and sum to 1."""


# ---------------------------------------------------------------- models

class ApiError(Exception):
    def __init__(self, msg, retryable):
        super().__init__(msg)
        self.retryable = retryable


def parse_spec(spec):
    """'gpt-x@high' -> ('gpt-x', 'high')."""
    model, _, effort = spec.partition("@")
    return model, (effort or None)


def call_openai(spec, system, user, args):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ApiError("OPENAI_API_KEY is not set", retryable=False)
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model, effort = parse_spec(spec)
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_object"},
    }
    if effort:
        body["reasoning_effort"] = effort
    if args.temperature is not None:
        body["temperature"] = args.temperature
    if args.max_tokens:
        body["max_completion_tokens"] = args.max_tokens
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        raise ApiError(f"HTTP {e.code}: {detail}", retryable=e.code in (408, 409, 429) or e.code >= 500)
    except (urllib.error.URLError, TimeoutError) as e:
        raise ApiError(f"network: {e}", retryable=True)
    choice = resp["choices"][0]
    usage = resp.get("usage") or {}
    return {
        "content": choice["message"].get("content") or "",
        "finish_reason": choice.get("finish_reason"),
        "served_model": resp.get("model"),
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
    }


def call_mock(spec, labels, seed):
    """Offline stand-ins for testing the pipeline."""
    rng = random.Random(seed)
    if spec == "mock-uniform":
        probs = {l: 1 / len(labels) for l in labels}
    elif spec == "mock-random":
        w = [rng.expovariate(1) for _ in labels]
        probs = {l: x / sum(w) for l, x in zip(labels, w)}
    elif spec == "mock-garbage":
        return {"content": "not json at all", "finish_reason": "stop", "served_model": spec}
    else:
        raise ApiError(f"unknown mock model {spec}", retryable=False)
    best = max(probs, key=probs.get)
    content = json.dumps({"reasoning": "mock", "probabilities": probs, "most_likely": best})
    return {"content": content, "finish_reason": "stop", "served_model": spec,
            "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0}


JEV_INSTRUCTIONS = (
    "An agent acts in the planning domain `domain_pddl`, starting from the objects and initial state "
    "in `problem_pddl`. Its goal is exactly one of the options, but you do not know which. "
    "`observed_actions` lists some of its actions in the order it performed them. The observation is "
    "partial: the agent may have performed other, unobserved actions before, between, or after the "
    "observed ones. The agent's full plan achieves its goal; every action costs 1, and the agent tends "
    "to pursue its goal with low-cost (efficient) plans. Which option is the agent's goal?"
)


def is_jev(spec):
    return spec.startswith("jev-")


def jev_order(labels, seed_key):
    """Option order for one Jev call, shuffled per (domain, k, sample) because
    jev-1.13 is known to lean toward the first option."""
    order = list(labels)
    random.Random(repr(seed_key)).shuffle(order)
    return order


def jev_request(spec, state, questions, args):
    """POST one System One request to TypeSafe; returns the parsed response."""
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise ApiError("TYPESAFE_API_KEY is not set", retryable=False)
    base = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai").rstrip("/")
    req = urllib.request.Request(
        f"{base}/v1/systemone",
        data=json.dumps({"model": spec, "state": state, "questions": questions}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        raise ApiError(f"HTTP {e.code}: {detail}", retryable=e.code in (408, 409, 429) or e.code >= 500)
    except (urllib.error.URLError, TimeoutError) as e:
        raise ApiError(f"network: {e}", retryable=True)


def call_jev(spec, dom, obs, order, args):
    """TypeSafe's Jev answers a Choice question with a probability per option, so
    the candidate goals become the options and no JSON parsing is involved. The
    answer is stored in the same JSON shape the chat models return."""
    hyps = dict(zip(dom["labels"], dom["hyps"]))
    resp = jev_request(
        spec,
        {"domain_pddl": dom["domain_pddl"], "problem_pddl": dom["problem_pddl"], "observed_actions": obs},
        {"goal": {
            "type": "choice",
            "instructions": JEV_INSTRUCTIONS,
            "criteria": {l: f"The agent's goal is (and {' '.join(hyps[l])})" for l in order},
        }},
        args)
    ans = resp["answers"]["goal"]
    usage = resp.get("usage") or {}
    content = json.dumps({"reasoning": None, "probabilities": ans["probabilities"],
                          "most_likely": ans["choice"], "confidence": ans.get("confidence")})
    return {"content": content, "finish_reason": "stop", "served_model": resp.get("model"),
            "option_order": order, "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"), "reasoning_tokens": None}


def call_hf(spec, system, user, seed, args):
    import nextaction  # lazy: pulls in torch/transformers only when an hf: model is used
    with nextaction._hf_lock:
        out = nextaction.hf_model(spec, args).generate(system, user, args.temperature,
                                                       args.max_tokens or 2048, seed)
    out["served_model"] = spec[3:]
    return out


def with_retries(fn, args):
    delay = 2.0
    for attempt in range(args.retries + 1):
        try:
            return fn()
        except ApiError as e:
            if not e.retryable or attempt == args.retries:
                raise
            time.sleep(delay + random.random())
            delay = min(delay * 2, 60)


def query(spec, system, user, labels, seed, args):
    """Chat-style models: mocks, hf: and OpenAI. Jev needs the structured task,
    so cmd_run calls call_jev directly."""
    if spec.startswith("mock-"):
        return call_mock(spec, labels, seed)
    if spec.startswith("hf:"):
        return call_hf(spec, system, user, seed, args)
    if is_jev(spec):
        raise ApiError(f"{spec} takes typed questions, not a chat prompt; use it from bench.py run",
                       retryable=False)
    return with_retries(lambda: call_openai(spec, system, user, args), args)


def missing_keys(specs):
    """Exit message if a spec's provider key is not in the environment."""
    need = set()
    for s in specs:
        if is_jev(s):
            need.add("TYPESAFE_API_KEY")
        elif not s.startswith(("mock-", "hf:")):
            need.add("OPENAI_API_KEY")
    missing = sorted(k for k in need if not os.environ.get(k))
    return f"{', '.join(missing)} not set. Export it in your shell first." if missing else None


# ---------------------------------------------------------------- run

def read_raw():
    if not RAW.exists():
        return []
    with RAW.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def record_key(r):
    return (r["model"], r["domain"], r["k"], r["sample"])


def cmd_run(args):
    RESULTS.mkdir(exist_ok=True)
    done = {record_key(r) for r in read_raw() if not r.get("error")}
    doms = {n: load_domain(n) for n in args.domains}
    jobs = []
    for spec in args.model:
        for n in args.domains:
            for k in args.evidence:
                for s in range(args.samples):
                    if (spec, n, k, s) not in done:
                        jobs.append((spec, n, k, s))
    print(f"{len(jobs)} calls to make ({len(done)} already done)")
    if args.dry_run:
        for j in jobs:
            print("  ", *j)
        return
    msg = missing_keys({j[0] for j in jobs})
    if msg:
        sys.exit(msg)

    lock = threading.Lock()

    def work(job):
        spec, n, k, s = job
        dom = doms[n]
        obs = load_evidence(n, k)
        rec = {"model": spec, "domain": n, "k": k, "sample": s, "time": time.time()}
        t0 = time.time()
        try:
            if is_jev(spec):
                order = jev_order(dom["labels"], (n, k, s))
                rec.update(with_retries(lambda: call_jev(spec, dom, obs, order, args), args))
            else:
                seed = hash(job) & 0xFFFFFFFF
                rec.update(query(spec, SYSTEM_PROMPT, build_prompt(dom, obs), dom["labels"], seed, args))
            rec["error"] = None
        except (ApiError, KeyError, ValueError, RuntimeError) as e:
            rec["error"] = str(e)
        rec["latency_s"] = round(time.time() - t0, 3)
        with lock:
            with RAW.open("a") as f:
                f.write(json.dumps(rec) + "\n")
        return rec

    failures = 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for i, rec in enumerate(ex.map(work, jobs), 1):
            status = "ERROR " + rec["error"][:120] if rec["error"] else "ok"
            failures += bool(rec["error"])
            print(f"[{i}/{len(jobs)}] {rec['model']} {rec['domain']} k={rec['k']} s={rec['sample']} "
                  f"{rec['latency_s']:.1f}s {status}", flush=True)
    print(f"done; {failures} failed (rerun the same command to retry them)")


# ---------------------------------------------------------------- scoring

def normalize(d):
    tot = sum(d.values())
    return {k: v / tot for k, v in d.items()} if tot > 0 else None


def parse_answer(content, labels):
    """Return (distribution, most_likely) or (None, None)."""
    try:
        obj = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        m = re.search(r"\{.*\}", content or "", re.S)
        try:
            obj = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            obj = None
    if not isinstance(obj, dict) or not isinstance(obj.get("probabilities"), dict):
        return None, None
    raw = {str(k).strip().lower(): v for k, v in obj["probabilities"].items()}
    dist = {}
    for l in labels:
        try:
            dist[l] = max(float(raw.get(l, 0.0)), 0.0)
        except (TypeError, ValueError):
            dist[l] = 0.0
    if not all(math.isfinite(v) for v in dist.values()):
        return None, None
    ml = str(obj.get("most_likely", "")).strip().lower()
    return normalize(dist), (ml if ml in labels else None)


def argmax_set(p):
    top = max(p.values())
    return {k for k, v in p.items() if v >= top - 1e-9}


def js_divergence(p, q):
    def kl(a, b):
        return sum(a[k] * math.log2(a[k] / b[k]) for k in a if a[k] > 0)
    m = {k: (p[k] + q[k]) / 2 for k in p}
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def score_dist(p, true, ref):
    labels = list(p)
    top = argmax_set(p)
    out = {
        "top1": (1 / len(top)) if true in top else 0.0,  # expected accuracy with random tie-break
        "p_true": p[true],
        # ties with other goals count as half a position each (mid-rank)
        "rank": 1 + sum(v > p[true] + 1e-9 for v in p.values())
                + (sum(abs(v - p[true]) <= 1e-9 for v in p.values()) - 1) / 2,
        "log_loss": -math.log(max(p[true], 1e-6)),
        "brier": sum((p[l] - (l == true)) ** 2 for l in labels),
        "entropy": -sum(v * math.log2(v) for v in p.values() if v > 0) / math.log2(len(labels)),
    }
    if "rg" in ref:
        q = ref["rg"]
        out["tv_rg"] = 0.5 * sum(abs(p[l] - q[l]) for l in labels)
        out["js_rg"] = js_divergence(p, q)
        out["agree_rg"] = len(top & argmax_set(q)) / len(top)
    return out


METRICS = ["top1", "ml_acc", "p_true", "rank", "log_loss", "brier", "entropy",
           "tv_rg", "js_rg", "agree_rg"]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def std(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def fmt(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def cmd_score(args):
    doms = {n: load_domain(n) for n in DOMAINS}
    refs = {(n, k): load_reference(n, k) for n in DOMAINS for k in EVIDENCE_LEVELS}

    latest = {}
    for r in read_raw():  # later records supersede earlier ones for the same key
        if r.get("error") and record_key(r) in latest and not latest[record_key(r)].get("error"):
            continue
        latest[record_key(r)] = r

    rows = []
    for r in latest.values():
        dom = doms[r["domain"]]
        ref = refs[(r["domain"], r["k"])]
        row = {"model": r["model"], "domain": r["domain"], "k": r["k"], "sample": r["sample"],
               "api_error": bool(r.get("error")), "valid": False,
               "input_tokens": r.get("input_tokens"), "output_tokens": r.get("output_tokens"),
               "reasoning_tokens": r.get("reasoning_tokens"), "latency_s": r.get("latency_s"),
               "finish_reason": r.get("finish_reason")}
        if not r.get("error"):
            p, ml = parse_answer(r.get("content"), dom["labels"])
            if p:
                row.update(valid=True, ml_acc=float(ml == dom["true"]), dist=p, **score_dist(p, dom["true"], ref))
        rows.append(row)

    # Baselines: computed, not sampled.
    base_rows = []
    for n, dom in doms.items():
        for k in EVIDENCE_LEVELS:
            ref = refs[(n, k)]
            cands = {"baseline:uniform": {l: 1 / len(dom["labels"]) for l in dom["labels"]}}
            if "map" in ref:
                cands["baseline:FiFO-MAP"] = {l: float(l == ref["map"]) for l in dom["labels"]}
            if "rg" in ref:
                cands["baseline:FiFO-R&G"] = ref["rg"]
            for name, p in cands.items():
                base_rows.append({"model": name, "domain": n, "k": k, "sample": 0, "valid": True,
                                  "api_error": False, "dist": p, **score_dist(p, dom["true"], ref)})

    RESULTS.mkdir(exist_ok=True)
    fields = ["model", "domain", "k", "sample", "api_error", "valid", "finish_reason", *METRICS,
              "input_tokens", "output_tokens", "reasoning_tokens", "latency_s"]
    with (RESULTS / "per_response.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fields, extrasaction="ignore")
        w.writeheader()
        for row in sorted(rows, key=lambda r: (r["model"], r["domain"], r["k"], r["sample"])):
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()})

    models = sorted({r["model"] for r in rows})
    groups = defaultdict(list)
    for r in rows + base_rows:
        groups[(r["model"], r["domain"], r["k"])].append(r)

    def agg(rs):
        ok = [r for r in rs if r["valid"]]
        a = {"n": len(rs), "valid_rate": len(ok) / len(rs) if rs else None}
        for m in METRICS:
            a[m] = mean([r.get(m) for r in ok])
            a[m + "_sd"] = std([r.get(m) for r in ok])
        for m in ["input_tokens", "output_tokens", "reasoning_tokens", "latency_s"]:
            a[m] = mean([r.get(m) for r in rs])
        if ok and len({(r["domain"], r["k"]) for r in rs}) == 1:  # ensemble = mean sampled distribution
            labels = list(ok[0]["dist"])
            ens = {l: sum(r["dist"][l] for r in ok) / len(ok) for l in labels}
            true = doms[rs[0]["domain"]]["true"]
            ref = refs[(rs[0]["domain"], rs[0]["k"])]
            e = score_dist(ens, true, ref)
            a["ens_top1"], a["ens_p_true"] = e["top1"], e["p_true"]
        return a

    summary = []
    for (m, n, k), rs in sorted(groups.items()):
        summary.append({"model": m, "domain": n, "k": k, **agg(rs)})
    with (RESULTS / "summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, list(summary[0].keys()) if summary else ["model"])
        w.writeheader()
        for s in summary:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()})

    all_names = models + sorted({r["model"] for r in base_rows})
    L = []
    L.append("# LLM plan-recognition results\n")
    L.append(f"True goals: BlockWords `{doms['blockwords']['true']}` (CORE, 21 candidates), "
             f"IntrusionDetection `{doms['intrusion']['true']}` (10 candidates). "
             "Chance top-1 = 0.048 / 0.10.\n")
    L.append("Metrics: **top-1** = expected accuracy of the argmax with random tie-breaking; "
             "**ML acc** = accuracy of the model's own `most_likely` field; **p(true)** = probability on the true goal; "
             "**rank** = position of the true goal (ties share the mid-rank; uniform over 21 goals = 11); **TV vs R&G** = total-variation distance "
             "to FiFO's Ramírez–Geffner posterior (k = 1, 3, 5 only; 0 = identical, 1 = disjoint); "
             "**agree R&G** = overlap of argmax with R&G's argmax. Means over valid responses.\n")

    L.append("## Overall (all domains, k = 1–5)\n")
    L.append("| model | responses | valid | top-1 | ML acc | p(true) | rank | log loss | Brier | TV vs R&G | agree R&G | in tok | out tok | reason tok | latency s |")
    L.append("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for m in all_names:
        rs = [r for r in rows + base_rows if r["model"] == m]
        if m.startswith("baseline:FiFO"):
            label = m + " (k=1,3,5)"
        else:
            label = m
        a = agg(rs)
        L.append(f"| {label} | {a['n']} | {fmt(a['valid_rate'])} | {fmt(a['top1'])} | {fmt(a['ml_acc'])} | "
                 f"{fmt(a['p_true'])} | {fmt(a['rank'], 1)} | {fmt(a['log_loss'])} | {fmt(a['brier'])} | "
                 f"{fmt(a['tv_rg'])} | {fmt(a['agree_rg'])} | {fmt(a['input_tokens'], 0)} | "
                 f"{fmt(a['output_tokens'], 0)} | {fmt(a['reasoning_tokens'], 0)} | {fmt(a['latency_s'], 1)} |")
    L.append("\nThe FiFO baselines exist only for k = 1, 3, 5, so compare them against the per-k tables below rather than this row.\n")

    for n, dom in doms.items():
        L.append(f"## {DOMAINS[n]} (true goal `{dom['true']}`)\n")
        L.append("| model | k | n | valid | top-1 | p(true) ± sd | rank | TV vs R&G | agree R&G | ensemble top-1 | ensemble p(true) |")
        L.append("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
        for k in EVIDENCE_LEVELS:
            for m in all_names:
                if (m, n, k) not in groups:
                    continue
                a = agg(groups[(m, n, k)])
                sd = f" ± {fmt(a['p_true_sd'])}" if a["p_true_sd"] is not None else ""
                L.append(f"| {m} | {k} | {a['n']} | {fmt(a['valid_rate'])} | {fmt(a['top1'])} | "
                         f"{fmt(a['p_true'])}{sd} | {fmt(a['rank'], 1)} | {fmt(a['tv_rg'])} | "
                         f"{fmt(a['agree_rg'])} | {fmt(a.get('ens_top1'))} | {fmt(a.get('ens_p_true'))} |")
        L.append("")

    bad = [r for r in rows if not r["valid"]]
    if bad:
        L.append("## Invalid or failed responses\n")
        L.append("| model | domain | k | sample | reason |")
        L.append("|---|---|--:|--:|---|")
        for r in sorted(bad, key=lambda r: (r["model"], r["domain"], r["k"], r["sample"])):
            why = "API error" if r["api_error"] else f"unparseable (finish_reason={r['finish_reason']})"
            L.append(f"| {r['model']} | {r['domain']} | {r['k']} | {r['sample']} | {why} |")
        L.append("")

    (RESULTS / "report.md").write_text("\n".join(L))
    print("\n".join(L))
    print(f"\nwrote {RESULTS / 'report.md'}, summary.csv, per_response.csv")


# ---------------------------------------------------------------- misc

def cmd_prompt(args):
    dom = load_domain(args.domain)
    print(build_prompt(dom, load_evidence(args.domain, args.k)))


def cmd_list_models(args):
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY is not set")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    req = urllib.request.Request(f"{base}/models", headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        ids = sorted(m["id"] for m in json.loads(r.read())["data"])
    print("\n".join(ids))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prompt", help="print one prompt")
    p.add_argument("domain", choices=DOMAINS)
    p.add_argument("k", type=int, choices=EVIDENCE_LEVELS)
    p.set_defaults(fn=cmd_prompt)

    p = sub.add_parser("list-models", help="list model ids available to your key")
    p.set_defaults(fn=cmd_list_models)

    p = sub.add_parser("run", help="query models")
    p.add_argument("--model", action="append", required=True,
                   help="repeatable: OpenAI id ('id@effort' sets reasoning_effort), jev-latest / jev-<version>, "
                        "hf:<name>, or mock-uniform/mock-random/mock-garbage (offline)")
    p.add_argument("--domains", nargs="+", choices=DOMAINS, default=list(DOMAINS))
    p.add_argument("--evidence", nargs="+", type=int, choices=EVIDENCE_LEVELS, default=EVIDENCE_LEVELS)
    p.add_argument("--samples", type=int, default=5, help="repeats per (model, domain, k)")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--temperature", type=float, default=None,
                   help="OpenAI: omit for reasoning models, which reject it; hf: sampling defaults to 1.0")
    p.add_argument("--max-tokens", type=int, default=None,
                   help="OpenAI max_completion_tokens; hf max_new_tokens (default 2048)")
    p.add_argument("--timeout", type=float, default=600)
    p.add_argument("--retries", type=int, default=5)
    p.add_argument("--device", default=None, help="hf: cuda / mps / cpu (default: best available)")
    p.add_argument("--dtype", default=None, help="hf: float16 / bfloat16 / float32")
    p.add_argument("--no-chat", action="store_true", help="hf: plain-text prompt instead of the chat template")
    p.add_argument("--dry-run", action="store_true", help="list the calls without making them")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("score", help="compute metrics and write the report")
    p.set_defaults(fn=cmd_score)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
