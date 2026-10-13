# LLM plan recognition on the FiFO benchmarks

Tests whether LLMs can do probabilistic goal recognition on the two
Ramírez & Geffner (AAAI-10) instances used in
[HenryKautz/FiFO](https://github.com/HenryKautz/FiFO) (`benchmarks.md`), and
compares them with FiFO's MAP and Ramírez–Geffner (R&G) results.

## Instances (`data/`)

Copied from `FiFO/SatPlan/Examples/Plan_Recognition/` (commit in
`data/SOURCE_COMMIT.txt`).

| Domain | Candidates | True goal | Evidence |
|---|--:|---|---|
| `blockwords` | 21 towers spelling words | `hyp16` (CORE) | first 1–5 of `unstack r p, pick-up o, unstack d a, unstack a c, pick-up c` |
| `intrusion` | 10 attacker objectives | `hyp0` (info gathered on all 10 hosts) | first 1–5 of `recon taurus, leo, virgo, sagittarius, cassiopea` |

`reference/` holds FiFO's R&G posteriors and MAP picks. They exist only for
k = 1, 3, 5, so metrics against R&G are reported for those levels only.

## Task

Each prompt gives the PDDL domain (with comments removed), the initial state,
the numbered candidate goals (labelled `hyp0`, `hyp1`, … in FiFO's order), and
the observed actions in order. It tells the model that observation is partial
and that the agent prefers low-cost plans (unit action costs). The model
returns JSON with a probability for every goal and a `most_likely` label. See
one with:

```bash
python3 bench.py prompt blockwords 3
```

## Running

Only Python 3 is needed; there is nothing to install. The key is read from the
environment and never written to disk.

```bash
export OPENAI_API_KEY=...        # your key
python3 bench.py list-models     # see which model ids you can use
python3 bench.py run --model MODEL_A --model MODEL_B@high --samples 5 --dry-run
python3 bench.py run --model MODEL_A --model MODEL_B@high --samples 5
python3 bench.py score           # writes results/report.md, summary.csv, per_response.csv
```

Other models in the same run, scored side by side with the GPT models:

```bash
export TYPESAFE_API_KEY=...      # TypeSafe's Jev (https://typesafe.ai)
python3 bench.py run --model jev-latest --samples 3
python3 bench.py run --model hf:Qwen/Qwen2.5-7B-Instruct --samples 3 --workers 1
python3 bench.py run --model hf:meta-llama/Meta-Llama-3-8B-Instruct --samples 3 --workers 1
```

- **Jev** (`jev-latest`, or a pinned version such as `jev-1.13.0`) is not a chat
  model: it answers typed questions with calibrated probabilities. Each call
  sends the domain PDDL, the problem and the observed actions as the `state`,
  and one *Choice* question whose options are the candidate goals (`hyp0`, …,
  each described by its goal conjunction), with the same task wording as the
  chat prompt. Jev's per-option probabilities are the distribution, and its
  `choice` is `most_likely`, so every response is valid and there is no
  reasoning text. Jev 1.13 is known to favour the first option, so sample 0
  lists the goals in FiFO's order and later samples shuffle them (the order is
  saved as `option_order` in `raw.jsonl`); its spread across samples measures
  order sensitivity, not sampling noise. `served_model` records the version
  behind the alias.
- **Qwen / Llama** run locally through transformers with the same prompt as
  the GPT models (the `hf:` backend shared with `nextaction.py`; needs
  `pip install torch transformers`). They sample at temperature 1.0 unless
  `--temperature` is set, generate up to 2048 new tokens (`--max-tokens`), and
  have no JSON mode, so the first `{...}` in the reply is parsed. On UVA HPC:
  `sbatch --export=ALL,MODEL=Qwen/Qwen2.5-7B-Instruct run_bench_hf.slurm`
  (likewise `MODEL=meta-llama/Meta-Llama-3-8B-Instruct`).
- `plot_curves.py` draws Jev, Qwen2.5-7B and Llama-3-8B next to the GPT
  models once they have results.
- `MODEL@effort` sends `reasoning_effort` (e.g. `low`/`medium`/`high`) and is
  scored as a separate model, so the same model at two efforts can be compared.
- The default is 2 domains × 5 evidence levels × `--samples` = 50 calls per
  model.
- Runs resume: raw responses are appended to `results/raw.jsonl`, and rerunning
  the same command only retries calls that are missing or failed.
- `--temperature` is off by default because reasoning models reject it.
- Set `OPENAI_BASE_URL` to use an OpenAI-compatible endpoint.
- `mock-uniform`, `mock-random` and `mock-garbage` run offline for testing.

## Metrics

| Metric | Meaning |
|---|---|
| valid | share of responses that parsed into a distribution |
| top-1 | the true goal is the argmax (ties split: a k-way tie scores 1/k) |
| ML acc | the model's own `most_likely` label is the true goal |
| p(true) | probability assigned to the true goal |
| rank | position of the true goal (ties share the mid-rank) |
| log loss, Brier | proper scoring rules against the true goal (lower is better) |
| TV / JS vs R&G | distance from FiFO's R&G posterior (k = 1, 3, 5) |
| agree R&G | the model's argmax overlaps R&G's argmax |
| ensemble | the same scores for the average of a setting's samples |
| tokens, latency | cost of each call |

Baselines appear in the same tables: `uniform`, `FiFO-MAP` (all mass on MAP's
pick) and `FiFO-R&G`.

Caveats: these are public benchmarks, so a model may have seen them during
training. The R&G posterior is a reference point, not ground truth: it assumes
β = 1 and uniform priors.

# Next-action prediction: comparing uncertainty estimators (`nextaction.py`)

Same two domains, but the model predicts the agent's **next action** instead
of its goal, and we compare three ways of getting a distribution out of an LLM.

**Decision points.** The benchmarks only give five observed actions with gaps,
so the current state, and with it "is this action applicable?", is undefined.
`nextaction.py plan` therefore builds one fully observed reference plan per
domain: the shortest plan for the true goal that contains the five observed
actions in order (BFS; ties go to doing the observed action first). It is saved
in `data/<domain>/reference_plan.txt`. Decision point *t* shows the first *t*
actions (complete, no gaps) and the target is action *t*+1: 10 points in
BlockWords (the canonical CORE plan) and 20 in IntrusionDetection. In
IntrusionDetection many next actions are equally optimal, so the realized one
is partly arbitrary and every estimator's accuracy there has a low ceiling.

**Pure-LLM candidate set.** All estimators produce a distribution over **all**
grounded actions (128 / 90; BlockWords excludes `stack x x`/`unstack x x`, as
the original domain's `(not (= ?x ?y))` guard does), never only the applicable
ones. The prompt lists the full vocabulary and never says which actions are
applicable, so no constraint information leaks in.

| estimator | how | models |
|---|---|---|
| `verbalized` | model lists its top-k actions with probabilities (default k = 5, 3 repeats); unassigned mass is spread uniformly over the unlisted actions | any |
| `sampling` | K independent single-action answers (default K = 10), counted | any, incl. black-box |
| `nexttoken` | log p(action string \| prompt) for every grounded action, softmax over the set | open models via `hf:<name>` |
| `nexttoken-preamble` | same, but the reply is prefilled with "I predict the agent's next action to be:\n\n" and each action pools `(name args)` + `name args` | open models via `hf:<name>` |

```bash
python3 nextaction.py plan                                  # show the reference plans
python3 nextaction.py prompt blockwords 3 --estimator verbalized
python3 nextaction.py run --estimator verbalized --model gpt-4.1 --samples 3
python3 nextaction.py run --estimator sampling   --model gpt-4.1 --samples 10
python3 nextaction.py run --estimator nexttoken  --model hf:Qwen/Qwen2.5-7B-Instruct
python3 nextaction.py run --estimator sampling   --model hf:Qwen/Qwen2.5-7B-Instruct --samples 10
python3 nextaction.py score    # results/nextaction/report.md, summary.csv, per_row.csv
```

Why the preamble: Llama-3-8B-Instruct almost always opens with a sentence
("Based on ..., I predict the agent's next action to be:\n\n(pick-up a)"), so
plain `nexttoken` only sees the 24% of its mass that starts with an action;
after the preamble 95% of the mass is on action strings. Prefilling a bare `(`
does not work: tokenizers merge it with the next letters (`(un`, `(p`, `(re`),
so a lone `(` token is off-distribution. `diag_firsttoken.py` prints each
model's top first tokens and greedy/sampled replies.

On UVA HPC, `run_hf.slurm` runs all estimators for one model
(`sbatch --export=ALL,MODEL=<hf repo>[,ESTIMATORS="nexttoken-preamble"] run_hf.slurm`).

`hf:` models need `pip install torch transformers` (the rest stays stdlib-only).
Running all three estimators on the same `hf:` model gives the cleanest
comparison. Runs resume like `bench.py`. Mocks: `mock-uniform`, `mock-random`
(verbalized/sampling) and `mock-lm` (nexttoken).

**Metrics:** top-1/3/5 accuracy (ties split), p(true), NLL of the true next
action (with ε = 0.01 uniform mass mixed into every estimator so a sampling
miss is finite; `--nll-eps`), multi-class Brier, top-label ECE (10 bins),
**invalid mass** (probability on grounded actions whose preconditions are false
in the true current state) and **ungrounded mass** (outputs matching no
grounded action). Each estimator also gets a **+mask** row, renormalized onto
the applicable actions: a preview of the constraint ablation. Baselines are
`uniform-all` and `uniform-applicable` (constraints only, no LLM).
