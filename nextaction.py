#!/usr/bin/env python3
"""Next-action prediction: compare three LLM uncertainty estimators.

Each decision point is a prefix of a fully observed reference plan; the model
predicts the next action as a distribution over ALL grounded actions (not just
the applicable ones), so the action constraints never leak into the pure-LLM
estimate.

Estimators:
  verbalized  the model states its top-k next actions with probabilities
  sampling    K independent samples of a single next action, counted
  nexttoken   log-probability of every grounded action string under an open
              model (Hugging Face transformers), renormalized over the set
  nexttoken-preamble  the same, but the reply is prefilled with the preamble
              the models write anyway ("I predict ... to be:\n\n") and each
              action's probability is pooled over "(name args)" and "name args"

Subcommands:
  plan     build/print the reference plans (data/<domain>/reference_plan.txt)
  prompt   print the prompt for one decision point
  run      query models; raw outputs go to results/nextaction/raw.jsonl
  score    write results/nextaction/report.md, summary.csv, per_row.csv

Model specs: OpenAI ids as in bench.py (`id@effort`), `hf:<repo-or-path>` for
a local transformers model, and offline mocks `mock-uniform`, `mock-random`,
`mock-lm`.
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
from collections import Counter, defaultdict, deque
from pathlib import Path

import bench
from bench import DATA, DOMAINS, ApiError, fmt, mean, strip_comments

OUT = Path(os.environ.get("NEXTACTION_OUT", bench.RESULTS / "nextaction"))
RAW = OUT / "raw.jsonl"
ESTIMATORS = ["verbalized", "sampling", "nexttoken", "nexttoken-preamble"]
# nexttoken-preamble prefills the reply with this (Llama-3's own wording). It ends
# on a line break, so the action after it tokenizes as it naturally would; a bare
# "(" prefill does not, because "(un", "(p", "(re" are single tokens.
PREAMBLE = "I predict the agent's next action to be:\n\n"


# ---------------------------------------------------------------- PDDL (STRIPS subset)

def sexp(text):
    toks = re.findall(r"\(|\)|[^\s()]+", strip_comments(text).lower())
    stack = [[]]
    for t in toks:
        if t == "(":
            stack.append([])
        elif t == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(t)
    return stack[0][0]


def typed_names(lst):
    """['?x', '?y', '-', 'block'] -> ['?x', '?y'] (types ignored: one type per domain)."""
    return [t for i, t in enumerate(lst) if t != "-" and (i == 0 or lst[i - 1] != "-")]


def conj(e):
    if not e:
        return [], []
    items = e[1:] if e[0] == "and" else [e]
    pos = [tuple(x) for x in items if x[0] != "not"]
    neg = [tuple(x[1]) for x in items if x[0] == "not"]
    return pos, neg


def field(form, key):
    i = form.index(key)
    return form[i + 1]


class Action:
    __slots__ = ("name", "args", "pre", "npre", "add", "dele", "text")

    def __init__(self, name, args, pre, npre, add, dele):
        self.name, self.args = name, args
        self.pre, self.npre, self.add, self.dele = frozenset(pre), frozenset(npre), frozenset(add), frozenset(dele)
        self.text = "(" + " ".join((name, *args)) + ")"

    def applicable(self, s):
        return self.pre <= s and not (self.npre & s)

    def apply(self, s):
        return (s - self.dele) | self.add


def ground(domain_text, objects):
    """All groundings with pairwise-distinct arguments (the original BlockWords
    domain guards stack/unstack with (not (= ?x ?y)); FiFO's copy drops it)."""
    import itertools
    acts = []
    for form in sexp(domain_text)[2:]:
        if form[0] != ":action":
            continue
        name = form[1]
        params = typed_names(field(form, ":parameters"))
        pre, npre = conj(field(form, ":precondition"))
        add, dele = conj(field(form, ":effect"))
        for combo in itertools.permutations(objects, len(params)):
            sub = dict(zip(params, combo))
            g = lambda atoms: [tuple(sub.get(t, t) for t in a) for a in atoms]
            acts.append(Action(name, combo, g(pre), g(npre), g(add), g(dele)))
    return acts


def atom_from_text(s):
    return tuple(s.strip("() ").split())


class World:
    """One benchmark domain: grounded actions, the reference plan and its states."""

    def __init__(self, name):
        self.name = name
        self.dom = bench.load_domain(name)
        prob = sexp((DATA / name / "template.pddl").read_text().replace("<HYPOTHESIS>", ""))
        self.objects = typed_names(next(f for f in prob[2:] if f[0] == ":objects")[1:])
        self.init = frozenset(tuple(a) for a in next(f for f in prob[2:] if f[0] == ":init")[1:])
        self.actions = ground((DATA / name / "domain.pddl").read_text(), self.objects)
        self.by_text = {a.text: a for a in self.actions}
        self.by_tokens = {(a.name, *a.args): a for a in self.actions}
        self.goal = frozenset(atom_from_text(a) for a in self.dom["hyps"][int(self.dom["true"][3:])])
        self.evidence = bench.load_evidence(name, max(bench.EVIDENCE_LEVELS))
        self.plan = self.load_or_build_plan()
        self.states = [self.init]
        for a in self.plan:
            act = self.by_text[a]
            assert act.applicable(self.states[-1]), f"{name}: {a} not applicable"
            self.states.append(act.apply(self.states[-1]))
        assert self.goal <= self.states[-1], f"{name}: reference plan misses the goal"

    def applicable(self, t):
        s = self.states[t]
        return {a.text for a in self.actions if a.applicable(s)}

    def relevant(self):
        """Backward relevance from the goal and the observed actions' preconditions."""
        obs = [self.by_text[o] for o in self.evidence]
        atoms = set(self.goal).union(*(o.pre for o in obs))
        rel = set(o.text for o in obs)
        changed = True
        while changed:
            changed = False
            for a in self.actions:
                if a.text not in rel and a.add & atoms:
                    rel.add(a.text)
                    atoms |= a.pre
                    changed = True
        return [a for a in self.actions if a.text in rel]

    def build_plan(self):
        """Shortest plan from init that contains the observed actions in order and
        reaches the true goal (BFS over (state, #observations matched)). Ties go
        to the next observed action, so observations happen as early as possible."""
        obs = self.evidence
        acts = sorted(self.relevant(), key=lambda a: a.text)
        start = (self.init, 0)
        parent = {start: None}
        q = deque([start])
        while q:
            node = q.popleft()
            s, i = node
            if i == len(obs) and self.goal <= s:
                plan = []
                while parent[node]:
                    node, a = parent[node]
                    plan.append(a)
                return plan[::-1]
            nxt_obs = obs[i] if i < len(obs) else None
            for a in sorted(acts, key=lambda a: a.text != nxt_obs):
                if a.applicable(s):
                    nxt = (a.apply(s), i + (i < len(obs) and a.text == obs[i]))
                    if nxt not in parent:
                        parent[nxt] = (node, a.text)
                        q.append(nxt)
        raise RuntimeError(f"{self.name}: no plan consistent with the evidence")

    def load_or_build_plan(self):
        p = DATA / self.name / "reference_plan.txt"
        if p.exists():
            return [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith(";")]
        plan = self.build_plan()
        p.write_text(
            ";; Shortest plan for the true goal that contains the 5 observed actions in order\n"
            ";; (generated by nextaction.py; delete this file to regenerate).\n" + "\n".join(plan) + "\n")
        return plan

    def parse_action(self, s):
        toks = tuple(re.sub(r"[(),]", " ", str(s).lower()).split())
        a = self.by_tokens.get(toks)
        return a.text if a else None


# ---------------------------------------------------------------- prompts

SYSTEM_JSON = bench.SYSTEM_PROMPT
SYSTEM_PLAIN = "You are an expert in automated planning and goal recognition."


def context(w, t):
    dom = w.dom
    goals = "\n".join(f"{lab}: (and {' '.join(h)})" for lab, h in zip(dom["labels"], dom["hyps"]))
    seen = "\n".join(f"{i + 1}. {a}" for i, a in enumerate(w.plan[:t])) or "(none yet: the agent has not acted)"
    acts = "\n".join(a.text for a in w.actions)
    return f"""Next-action prediction task.

An agent acts in the planning domain below, starting from the given initial state. Its goal is exactly one of the candidate goals listed, but you do not know which. Every action costs 1, and the agent tends to pursue its goal with low-cost (efficient) plans.

You have observed every action the agent has taken so far, in order, with nothing missing. Predict the agent's next action.

## Domain (PDDL)
{dom['domain_pddl']}

## Problem: objects and initial state (PDDL)
{dom['problem_pddl']}

## Candidate goals
{goals}

## Actions taken so far (complete, in order)
{seen}

## Action vocabulary
Actions are written as (name arg1 arg2 ...). These are all {len(w.actions)} grounded actions of the problem:
{acts}"""


def build_prompt(w, t, estimator, top_k):
    ctx = context(w, t)
    if estimator == "verbalized":
        return SYSTEM_JSON, ctx + f"""

## What to return
Give the {top_k} actions you consider most likely to be the agent's next action, each with your probability that it is the next action. Respond with a JSON object of this form:
{{
  "reasoning": "<brief explanation>",
  "top_actions": [{{"action": "(name arg1 ...)", "probability": <number>}}, ...]
}}
List at most {top_k} distinct actions from the vocabulary, most likely first. The probabilities must be non-negative and sum to at most 1; any remaining mass is treated as spread over the actions you did not list."""
    if estimator == "sampling":
        return SYSTEM_JSON, ctx + """

## What to return
Respond with a JSON object of this form:
{
  "reasoning": "<brief explanation>",
  "action": "(name arg1 ...)"
}
The action must be one action from the vocabulary: your best guess for the agent's next action."""
    if estimator.startswith("nexttoken"):
        return SYSTEM_PLAIN, ctx + "\n\nRespond with only the agent's next action, written exactly as in the vocabulary."
    raise ValueError(estimator)


# ---------------------------------------------------------------- open-model backend

class HFModel:
    """Local transformers model: scores continuations and samples text."""

    def __init__(self, name, device=None, dtype=None, chat=True):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        if dtype is None:
            dtype = {"cuda": "bfloat16", "mps": "float16"}.get(device, "float32")
        self.device = device
        self.tok = AutoTokenizer.from_pretrained(name)
        self.model = AutoModelForCausalLM.from_pretrained(name, dtype=getattr(torch, dtype)).to(device).eval()
        self.chat = chat and bool(getattr(self.tok, "chat_template", None))

    def render(self, system, user):
        if not self.chat:
            return f"{system}\n\n{user}\n\nNext action: "
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        try:
            return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except Exception:  # templates without a system role
            msgs = [{"role": "user", "content": system + "\n\n" + user}]
            return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)

    def encode(self, text):
        # Chat templates already carry the BOS token in their text.
        return self.tok(text, add_special_tokens=not self.chat).input_ids

    def score(self, system, user, conts, batch_size=32, prefill=""):
        """Return ({cont: log p(cont | prompt + prefill)}, #context tokens)."""
        torch = self.torch
        text = self.render(system, user) + prefill
        ctx = self.encode(text)
        cont_ids = []
        for c in conts:
            whole = self.encode(text + c)  # lm-eval style split, so the boundary token merges naturally
            cont_ids.append(whole[len(ctx):] if whole[:len(ctx)] == ctx else
                            self.tok(c, add_special_tokens=False).input_ids)
        out = {}
        with torch.no_grad():
            first = self.model(torch.tensor([ctx], device=self.device), use_cache=True)
            last = first.logits[0, -1].float().log_softmax(-1)
            for b in range(0, len(conts), batch_size):
                ids = cont_ids[b:b + batch_size]
                n, L = len(ids), max(map(len, ids))
                inp = torch.zeros(n, L, dtype=torch.long, device=self.device)
                mask = torch.zeros(n, len(ctx) + L, dtype=torch.long, device=self.device)
                mask[:, :len(ctx)] = 1
                for i, x in enumerate(ids):
                    inp[i, :len(x)] = torch.tensor(x)
                    mask[i, len(ctx):len(ctx) + len(x)] = 1
                logits = self.model(input_ids=inp, attention_mask=mask,
                                    past_key_values=self.expand_cache(first.past_key_values, n)).logits
                lp = logits.float().log_softmax(-1)
                for i, x in enumerate(ids):
                    s = last[x[0]].item()
                    for j in range(1, len(x)):
                        s += lp[i, j - 1, x[j]].item()
                    out[conts[b + i]] = s
        return out, len(ctx)

    def expand_cache(self, cache, n):
        import copy
        if hasattr(cache, "batch_repeat_interleave"):  # DynamicCache
            c = copy.deepcopy(cache)
            c.batch_repeat_interleave(n)
            return c
        return tuple(tuple(t.expand(n, *t.shape[1:]).contiguous() for t in layer) for layer in cache)

    def generate(self, system, user, temperature, max_new_tokens, seed):
        torch = self.torch
        torch.manual_seed(seed)
        ids = torch.tensor([self.encode(self.render(system, user))], device=self.device)
        with torch.no_grad():
            gen = self.model.generate(ids, attention_mask=torch.ones_like(ids), do_sample=True,
                                      temperature=temperature or 1.0, top_p=1.0, top_k=0,
                                      max_new_tokens=max_new_tokens, pad_token_id=self.tok.eos_token_id)
        new = gen[0, ids.shape[1]:]
        return {"content": self.tok.decode(new, skip_special_tokens=True), "served_model": "hf",
                "input_tokens": ids.shape[1], "output_tokens": len(new), "finish_reason": "stop"}


_hf = {}
_hf_lock = threading.Lock()


def hf_model(spec, args):
    if spec not in _hf:
        _hf[spec] = HFModel(spec[3:], args.device, args.dtype, chat=not args.no_chat)
    return _hf[spec]


# ---------------------------------------------------------------- calls

def mock_generate(spec, w, estimator, top_k, seed):
    rng = random.Random(seed)
    texts = [a.text for a in w.actions]
    if estimator == "verbalized":
        picks = rng.sample(texts, top_k)
        if spec == "mock-uniform":
            ws = [1 / len(texts)] * top_k
        else:
            raw = [rng.expovariate(1) for _ in picks]
            ws = [x / sum(raw) * 0.9 for x in raw]
        obj = {"reasoning": "mock", "top_actions": [{"action": p, "probability": q} for p, q in zip(picks, ws)]}
    else:
        obj = {"reasoning": "mock", "action": rng.choice(texts + ["(fly-away x)"])}
    return {"content": json.dumps(obj), "finish_reason": "stop", "served_model": spec,
            "input_tokens": 0, "output_tokens": 0}


def do_call(job, worlds, args):
    estimator, spec, n, t, s = job
    w = worlds[n]
    system, user = build_prompt(w, t, estimator, args.top_k)
    seed = hash((spec, n, t, s, estimator)) & 0xFFFFFFFF
    if estimator.startswith("nexttoken"):
        texts = [a.text for a in w.actions]
        if estimator == "nexttoken":
            if spec == "mock-lm":
                rng = random.Random(seed)
                return {"logprobs": {c: -rng.expovariate(0.3) - 5 for c in texts}, "input_tokens": 0}
            with _hf_lock:
                lps, n_ctx = hf_model(spec, args).score(system, user, texts, args.batch_size)
            return {"logprobs": lps, "input_tokens": n_ctx}
        # nexttoken-preamble: pool "(name args)" and "name args" after the preamble.
        # No bare form is a prefix of another (object names are not prefixes of
        # each other), so the pooled events are disjoint.
        bare = [c[1:-1] for c in texts]
        if spec == "mock-lm":
            rng = random.Random(seed)
            lps = {c: -rng.expovariate(0.3) - 5 for c in texts + bare}
            n_ctx, pre = 0, -rng.expovariate(1)
        else:
            with _hf_lock:
                m = hf_model(spec, args)
                lps, n_ctx = m.score(system, user, texts + bare, args.batch_size, PREAMBLE)
                pre = m.score(system, user, [PREAMBLE], 1)[0][PREAMBLE]
        return {"logprobs": {c: logaddexp(lps[c], lps[b]) for c, b in zip(texts, bare)},
                "logprobs_paren": {c: lps[c] for c in texts},
                "logprobs_bare": {c: lps[b] for c, b in zip(texts, bare)},
                "prefill_logprob": pre, "input_tokens": n_ctx}
    if spec.startswith("mock-"):
        return mock_generate(spec, w, estimator, args.top_k, seed)
    if spec.startswith("hf:"):
        with _hf_lock:
            return hf_model(spec, args).generate(system, user, args.temperature, args.max_tokens or 1024, seed)
    return bench.query(spec, system, user, None, seed, args)


def logaddexp(a, b):
    m = max(a, b)
    return m + math.log(math.exp(a - m) + math.exp(b - m))


def read_raw():
    if not RAW.exists():
        return []
    with RAW.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def key(r):
    return (r["estimator"], r["model"], r["domain"], r["t"], r["sample"])


def cmd_run(args):
    OUT.mkdir(parents=True, exist_ok=True)
    worlds = {n: World(n) for n in args.domains}
    done = {key(r) for r in read_raw() if not r.get("error")}
    n_samples = 1 if args.estimator.startswith("nexttoken") else args.samples
    jobs = []
    for spec in args.model:
        if bench.is_jev(spec):
            sys.exit(f"{spec} is only wired into bench.py (goal recognition), not next-action prediction")
        if args.estimator.startswith("nexttoken") and not (spec.startswith("hf:") or spec == "mock-lm"):
            sys.exit(f"{args.estimator} needs an open model (hf:<name>) or mock-lm, not {spec}")
        for n in args.domains:
            steps = args.steps if args.steps else range(len(worlds[n].plan))
            for t in steps:
                if t >= len(worlds[n].plan):
                    continue
                for s in range(n_samples):
                    if (args.estimator, spec, n, t, s) not in done:
                        jobs.append((args.estimator, spec, n, t, s))
    print(f"{len(jobs)} calls to make ({len(done)} records already done)")
    if args.dry_run:
        for j in jobs:
            print("  ", *j)
        return
    api = [j for j in jobs if not (j[1].startswith(("mock-", "hf:")))]
    if api and not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set. Export it in your shell first.")

    lock = threading.Lock()

    def work(job):
        estimator, spec, n, t, s = job
        rec = {"estimator": estimator, "model": spec, "domain": n, "t": t, "sample": s, "time": time.time()}
        t0 = time.time()
        try:
            rec.update(do_call(job, worlds, args))
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
            print(f"[{i}/{len(jobs)}] {rec['estimator']} {rec['model']} {rec['domain']} t={rec['t']} "
                  f"s={rec['sample']} {rec['latency_s']:.1f}s {status}", flush=True)
    print(f"done; {failures} failed (rerun the same command to retry them)")


# ---------------------------------------------------------------- distributions

def load_json(content):
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        m = re.search(r"\{.*\}", content or "", re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            return None


def parse_verbalized(w, content):
    """-> (dist over grounded actions, ungrounded mass) or None.
    Listed mass is normalized only if it exceeds 1; the remainder is spread
    uniformly over the unlisted grounded actions."""
    obj = load_json(content)
    if not isinstance(obj, dict) or not isinstance(obj.get("top_actions"), list):
        return None
    listed, ungrounded = defaultdict(float), 0.0
    for item in obj["top_actions"]:
        if not isinstance(item, dict):
            continue
        try:
            q = max(float(item.get("probability", 0)), 0.0)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(q):
            continue
        a = w.parse_action(item.get("action", ""))
        if a:
            listed[a] += q
        else:
            ungrounded += q
    tot = sum(listed.values()) + ungrounded
    if tot <= 0:
        return None
    if tot > 1:
        listed = {a: q / tot for a, q in listed.items()}
        ungrounded /= tot
        tot = 1.0
    rest = [a.text for a in w.actions if a.text not in listed]
    p = {a.text: listed.get(a.text, 0.0) for a in w.actions}
    for a in rest:
        p[a] += (1 - tot) / len(rest)
    return p, ungrounded


def parse_sample(w, content):
    """-> grounded action text, '<ungrounded>' or None (unparseable)."""
    obj = load_json(content)
    if not isinstance(obj, dict) or "action" not in obj:
        return None
    return w.parse_action(obj["action"]) or "<ungrounded>"


def softmax(lps):
    m = max(lps.values())
    z = sum(math.exp(v - m) for v in lps.values())
    return {k: math.exp(v - m) / z for k, v in lps.items()}, m + math.log(z)


# ---------------------------------------------------------------- metrics

def score_dist(p, true, applicable, ungrounded, eps):
    """p: grounded action -> prob (sums to 1 - ungrounded)."""
    n = len(p)
    pt = p[true]
    greater = sum(v > pt + 1e-12 for v in p.values())
    ties = sum(abs(v - pt) <= 1e-12 for v in p.values())
    topk = {f"top{k}": min(max((k - greater) / ties, 0.0), 1.0) for k in (1, 3, 5)}
    conf = max(p.values())
    return {
        **topk,
        "p_true": pt,
        "nll": -math.log((1 - eps) * pt + eps / n),
        "brier": sum((v - (a == true)) ** 2 for a, v in p.items()) + ungrounded ** 2,
        "invalid": sum(v for a, v in p.items() if a not in applicable),
        "ungrounded": ungrounded,
        "conf": conf,
        "n_applicable": len(applicable),
    }


def mask(p, applicable):
    """Constraint ablation: renormalize onto the applicable actions."""
    z = sum(p[a] for a in applicable)
    if z <= 0:
        return {a: (1 / len(applicable) if a in applicable else 0.0) for a in p}
    return {a: (v / z if a in applicable else 0.0) for a, v in p.items()}


def ece(rows, bins=10):
    rows = [r for r in rows if r.get("conf") is not None]
    if not rows:
        return None
    by = defaultdict(list)
    for r in rows:
        by[min(int(r["conf"] * bins), bins - 1)].append(r)
    return sum(len(b) / len(rows) * abs(mean([r["conf"] for r in b]) - mean([r["top1"] for r in b]))
               for b in by.values())


METRICS = ["top1", "top3", "top5", "p_true", "nll", "brier", "invalid", "ungrounded"]


def cmd_score(args):
    worlds = {n: World(n) for n in DOMAINS}
    applic = {(n, t): worlds[n].applicable(t) for n in worlds for t in range(len(worlds[n].plan))}
    latest = {}
    for r in read_raw():
        if r.get("error") and key(r) in latest and not latest[key(r)].get("error"):
            continue
        latest[key(r)] = r

    # One row per (estimator, model, domain, t[, sample]) with a distribution.
    dists = []  # (estimator, model, domain, t, sample, p, ungrounded, cost dict)
    invalid_resp = Counter()
    total_resp = Counter()
    groups = defaultdict(list)
    for r in latest.values():
        groups[(r["estimator"], r["model"], r["domain"], r["t"])].append(r)
    for (est, m, n, t), rs in sorted(groups.items()):
        w = worlds[n]
        cost = {"calls": len(rs), "input_tokens": sum(r.get("input_tokens") or 0 for r in rs),
                "output_tokens": sum(r.get("output_tokens") or 0 for r in rs)}
        total_resp[(est, m)] += len(rs)
        if est.startswith("nexttoken"):
            r = rs[0]
            if r.get("error"):
                invalid_resp[(est, m)] += 1
                continue
            p, logz = softmax(r["logprobs"])
            extra = {"grounded_mass": math.exp(logz)}
            if "prefill_logprob" in r:
                extra["prefill_prob"] = math.exp(r["prefill_logprob"])
            if "logprobs_bare" in r:  # share of the pooled grounded mass written without parentheses
                bare = sum(math.exp(v) for v in r["logprobs_bare"].values())
                extra["bare_share"] = bare / math.exp(logz)
            dists.append((est, m, n, t, 0, p, 0.0, {**cost, **extra}))
        elif est == "verbalized":
            ok = []
            for r in sorted(rs, key=lambda r: r["sample"]):
                parsed = None if r.get("error") else parse_verbalized(w, r.get("content"))
                if parsed is None:
                    invalid_resp[(est, m)] += 1
                    continue
                ok.append(parsed)
                dists.append((est, m, n, t, r["sample"], *parsed, {**cost, "calls": 1}))
            if len(ok) > 1:  # mean of the stated distributions
                p = {a: mean([d[0][a] for d in ok]) for a in ok[0][0]}
                dists.append(("verbalized-mean", m, n, t, 0, p, mean([d[1] for d in ok]), cost))
        elif est == "sampling":
            draws = []
            for r in rs:
                a = None if r.get("error") else parse_sample(w, r.get("content"))
                if a is None:
                    invalid_resp[(est, m)] += 1
                else:
                    draws.append(a)
            if not draws:
                continue
            c = Counter(draws)
            p = {a.text: c[a.text] / len(draws) for a in w.actions}
            dists.append((f"sampling-K{len(draws)}" if args.label_k else est, m, n, t, 0, p,
                          c["<ungrounded>"] / len(draws), cost))

    for n, w in worlds.items():  # baselines
        for t in range(len(w.plan)):
            A = applic[(n, t)]
            dists.append(("baseline", "uniform-all", n, t, 0, {a.text: 1 / len(w.actions) for a in w.actions}, 0.0, {}))
            dists.append(("baseline", "uniform-applicable", n, t, 0,
                          {a.text: (1 / len(A) if a.text in A else 0.0) for a in w.actions}, 0.0, {}))

    rows = []
    for est, m, n, t, s, p, ung, cost in dists:
        A, true = applic[(n, t)], worlds[n].plan[t]
        base = {"estimator": est, "model": m, "domain": n, "t": t, "sample": s, **cost}
        rows.append({**base, "masked": False, **score_dist(p, true, A, ung, args.nll_eps)})
        if est != "baseline":
            rows.append({**base, "masked": True, **score_dist(mask(p, A), true, A, 0.0, args.nll_eps)})

    OUT.mkdir(parents=True, exist_ok=True)
    fields = ["estimator", "model", "masked", "domain", "t", "sample", *METRICS, "conf", "n_applicable",
              "grounded_mass", "prefill_prob", "bare_share", "calls", "input_tokens", "output_tokens"]
    with (OUT / "per_row.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fields, extrasaction="ignore")
        wr.writeheader()
        for r in rows:
            wr.writerow({k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items()})

    def agg(rs):
        # Average within each decision point first, so settings with more samples don't weigh more.
        per_t = defaultdict(list)
        for r in rs:
            per_t[(r["domain"], r["t"])].append(r)
        a = {m_: mean([mean([r[m_] for r in g]) for g in per_t.values()]) for m_ in METRICS}
        a["ece"] = ece(rs)
        a["points"] = len(per_t)
        a["rows"] = len(rs)
        a["calls_per_point"] = mean([mean([r.get("calls") for r in g]) for g in per_t.values()])
        a["tokens_per_point"] = mean([mean([(r.get("input_tokens") or 0) + (r.get("output_tokens") or 0)
                                            for r in g]) for g in per_t.values()])
        a["grounded_mass"] = mean([r.get("grounded_mass") for r in rs])
        a["prefill_prob"] = mean([r.get("prefill_prob") for r in rs])
        a["bare_share"] = mean([r.get("bare_share") for r in rs])
        return a

    settings = sorted({(r["estimator"], r["model"], r["masked"]) for r in rows},
                      key=lambda x: (x[0] == "baseline", x[2], x[0], x[1]))
    summary = []
    for est, m, msk in settings:
        for n in [None, *worlds]:
            rs = [r for r in rows if (r["estimator"], r["model"], r["masked"]) == (est, m, msk)
                  and (n is None or r["domain"] == n)]
            if rs:
                summary.append({"estimator": est, "model": m, "masked": msk, "domain": n or "all", **agg(rs)})
    with (OUT / "summary.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, list(summary[0]))
        wr.writeheader()
        for s in summary:
            wr.writerow({k: (round(v, 5) if isinstance(v, float) else v) for k, v in s.items()})

    L = ["# Next-action prediction: uncertainty estimators\n"]
    L.append("Decision point *t* = the agent has taken the first *t* actions of the reference plan "
             "(`data/<domain>/reference_plan.txt`); the target is action *t*+1. Every estimator is a "
             "distribution over **all** grounded actions, applicable or not.\n")
    for n, w in worlds.items():
        L.append(f"- **{DOMAINS[n]}**: {len(w.plan)} decision points, {len(w.actions)} grounded actions, "
                 f"{min(len(applic[(n, t)]) for t in range(len(w.plan)))}–"
                 f"{max(len(applic[(n, t)]) for t in range(len(w.plan)))} applicable per step.")
    L.append("")
    L.append(f"Metrics (means over decision points; samples are averaged within a point first): "
             f"**top-k** = true action in the top k (ties split); **NLL** = −log p(true) after mixing "
             f"ε = {args.nll_eps} of uniform mass into every estimator, so a zero-probability miss costs "
             f"−log(ε/|A|) instead of ∞; **Brier** = multi-class, over grounded actions plus ungrounded mass; "
             f"**ECE** = top-label calibration, 10 bins, pooled over rows; **invalid** = mass on grounded actions "
             f"whose preconditions are false in the true current state; **ungrounded** = mass on outputs that "
             f"match no grounded action. Rows marked **+mask** are the same outputs renormalized onto the "
             f"applicable actions (the constraint ablation), so their invalid mass is 0 by construction.\n")
    if invalid_resp:
        L.append("Unparseable or failed responses: " + ", ".join(
            f"{e}/{m} {invalid_resp[(e, m)]}/{total_resp[(e, m)]}" for e, m in sorted(invalid_resp)) + ".\n")

    for n in ["all", *worlds]:
        title = "All domains" if n == "all" else DOMAINS[n]
        L.append(f"## {title}\n")
        L.append("| estimator | model | points | top-1 | top-3 | top-5 | p(true) | NLL | Brier | ECE | invalid | ungrounded | calls/pt | tokens/pt |")
        L.append("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
        for s in summary:
            if s["domain"] != n:
                continue
            est = s["estimator"] + (" +mask" if s["masked"] else "")
            L.append(f"| {est} | {s['model']} | {s['points']} | {fmt(s['top1'])} | {fmt(s['top3'])} | "
                     f"{fmt(s['top5'])} | {fmt(s['p_true'])} | {fmt(s['nll'])} | {fmt(s['brier'])} | "
                     f"{fmt(s['ece'])} | {fmt(s['invalid'])} | {fmt(s['ungrounded'])} | "
                     f"{fmt(s['calls_per_point'], 1)} | {fmt(s['tokens_per_point'], 0)} |")
        L.append("")
    gm = [s for s in summary if s["estimator"].startswith("nexttoken") and s["domain"] == "all" and not s["masked"]]
    if gm:
        L.append("Next-token: share of the model's reply probability that falls on the grounded action "
                 "strings at all, before renormalizing. For `nexttoken-preamble` this is given the preamble "
                 f"{PREAMBLE.strip()!r} and pools `(name args)` with `name args`; *bare share* is the part of it "
                 "written without parentheses, and *p(preamble)* is how likely the model was to write that exact "
                 "preamble unprompted:\n")
        L.append("| estimator | model | grounded mass | bare share | p(preamble) |")
        L.append("|---|---|--:|--:|--:|")
        for s in gm:
            L.append(f"| {s['estimator']} | {s['model']} | {fmt(s['grounded_mass'], 3)} | "
                     f"{fmt(s['bare_share'], 3)} | {fmt(s['prefill_prob'], 4)} |")
        L.append("")
    (OUT / "report.md").write_text("\n".join(L))
    print("\n".join(L))
    print(f"wrote {OUT / 'report.md'}, summary.csv, per_row.csv")


# ---------------------------------------------------------------- misc

def cmd_plan(args):
    for n in args.domains:
        p = DATA / n / "reference_plan.txt"
        if args.rebuild and p.exists():
            p.unlink()
        w = World(n)
        print(f"== {DOMAINS[n]}: {len(w.plan)} steps, {len(w.actions)} grounded actions "
              f"(observed: {', '.join(w.evidence)})")
        for t, a in enumerate(w.plan):
            mark = "*" if a in w.evidence else " "
            print(f"  t={t:2d} {mark} {a:30s} applicable={len(w.applicable(t))}")


def cmd_prompt(args):
    w = World(args.domain)
    system, user = build_prompt(w, args.t, args.estimator, args.top_k)
    print(f"[system] {system}\n\n{user}\n\n[target] {w.plan[args.t]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="build/print the reference plans")
    p.add_argument("--domains", nargs="+", choices=DOMAINS, default=list(DOMAINS))
    p.add_argument("--rebuild", action="store_true")
    p.set_defaults(fn=cmd_plan)

    p = sub.add_parser("prompt", help="print one prompt")
    p.add_argument("domain", choices=DOMAINS)
    p.add_argument("t", type=int)
    p.add_argument("--estimator", choices=ESTIMATORS, default="verbalized")
    p.add_argument("--top-k", type=int, default=5)
    p.set_defaults(fn=cmd_prompt)

    p = sub.add_parser("run", help="query models")
    p.add_argument("--estimator", choices=ESTIMATORS, required=True)
    p.add_argument("--model", action="append", required=True,
                   help="repeatable: OpenAI id[@effort], hf:<name>, mock-uniform, mock-random, mock-lm")
    p.add_argument("--domains", nargs="+", choices=DOMAINS, default=list(DOMAINS))
    p.add_argument("--steps", nargs="+", type=int, help="decision points t (default: all)")
    p.add_argument("--samples", type=int, default=None,
                   help="verbalized: repeats per point (default 3); sampling: K (default 10)")
    p.add_argument("--top-k", type=int, default=5, help="verbalized: how many actions to list")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--temperature", type=float, default=None,
                   help="OpenAI: omitted unless set (reasoning models reject it); hf sampling defaults to 1.0")
    p.add_argument("--max-tokens", type=int, default=None)
    p.add_argument("--timeout", type=float, default=600)
    p.add_argument("--retries", type=int, default=5)
    p.add_argument("--device", default=None, help="hf: cuda / mps / cpu (default: best available)")
    p.add_argument("--dtype", default=None, help="hf: float16 / bfloat16 / float32")
    p.add_argument("--batch-size", type=int, default=32, help="nexttoken: continuations per forward pass")
    p.add_argument("--no-chat", action="store_true", help="hf: plain-text prompt instead of the chat template")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("score", help="compute metrics and write the report")
    p.add_argument("--nll-eps", type=float, default=0.01, help="uniform mass mixed in before NLL")
    p.add_argument("--label-k", action="store_true", help="name sampling rows by their K")
    p.set_defaults(fn=cmd_score)

    args = ap.parse_args()
    if getattr(args, "samples", 0) is None:
        args.samples = {"verbalized": 3, "sampling": 10}.get(args.estimator, 1)
    args.fn(args)


if __name__ == "__main__":
    main()
