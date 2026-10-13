# Next-action prediction: uncertainty estimators

Decision point *t* = the agent has taken the first *t* actions of the reference plan (`data/<domain>/reference_plan.txt`); the target is action *t*+1. Every estimator is a distribution over **all** grounded actions, applicable or not.

- **BlockWords**: 10 decision points, 128 grounded actions, 4–6 applicable per step.
- **IntrusionDetection**: 20 decision points, 90 grounded actions, 10–30 applicable per step.

Metrics (means over decision points; samples are averaged within a point first): **top-k** = true action in the top k (ties split); **NLL** = −log p(true) after mixing ε = 0.01 of uniform mass into every estimator, so a zero-probability miss costs −log(ε/|A|) instead of ∞; **Brier** = multi-class, over grounded actions plus ungrounded mass; **ECE** = top-label calibration, 10 bins, pooled over rows; **invalid** = mass on grounded actions whose preconditions are false in the true current state; **ungrounded** = mass on outputs that match no grounded action. Rows marked **+mask** are the same outputs renormalized onto the applicable actions (the constraint ablation), so their invalid mass is 0 by construction.

Unparseable or failed responses: sampling/hf:Qwen/Qwen2.5-7B-Instruct 2/300, sampling/hf:meta-llama/Meta-Llama-3-8B-Instruct 5/300, verbalized/hf:Qwen/Qwen2.5-7B-Instruct 1/90, verbalized/hf:meta-llama/Meta-Llama-3-8B-Instruct 2/90.

## All domains

| estimator | model | points | top-1 | top-3 | top-5 | p(true) | NLL | Brier | ECE | invalid | ungrounded | calls/pt | tokens/pt |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| nexttoken | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.10 | 0.30 | 0.47 | 0.11 | 4.95 | 1.26 | 0.50 | 0.34 | 0.00 | 1.0 | 1832 |
| nexttoken | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.10 | 0.20 | 0.23 | 0.04 | 5.09 | 1.09 | 0.27 | 0.53 | 0.00 | 1.0 | 1826 |
| nexttoken-preamble | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.07 | 0.37 | 0.43 | 0.12 | 4.97 | 1.23 | 0.53 | 0.35 | 0.00 | 1.0 | 1842 |
| nexttoken-preamble | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.03 | 0.27 | 0.30 | 0.08 | 4.58 | 1.06 | 0.32 | 0.51 | 0.00 | 1.0 | 1836 |
| sampling | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.13 | 0.25 | 0.33 | 0.09 | 6.48 | 1.11 | 0.26 | 0.40 | 0.04 | 10.0 | 19725 |
| sampling | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.13 | 0.25 | 0.27 | 0.08 | 6.91 | 1.07 | 0.23 | 0.47 | 0.01 | 10.0 | 19338 |
| verbalized | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.10 | 0.21 | 0.24 | 0.07 | 6.74 | 1.11 | 0.27 | 0.54 | 0.02 | 1.0 | 6349 |
| verbalized | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.05 | 0.16 | 0.21 | 0.04 | 5.71 | 1.11 | 0.26 | 0.59 | 0.01 | 1.0 | 6266 |
| verbalized-mean | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.13 | 0.17 | 0.30 | 0.07 | 5.24 | 1.00 | 0.19 | 0.54 | 0.02 | 3.0 | 6349 |
| verbalized-mean | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.10 | 0.17 | 0.30 | 0.04 | 4.95 | 1.02 | 0.10 | 0.59 | 0.01 | 3.0 | 6266 |
| nexttoken +mask | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.17 | 0.43 | 0.77 | 0.19 | 4.06 | 1.18 | 0.49 | 0.00 | 0.00 | 1.0 | 1832 |
| nexttoken +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.13 | 0.33 | 0.57 | 0.13 | 4.18 | 1.17 | 0.49 | 0.00 | 0.00 | 1.0 | 1826 |
| nexttoken-preamble +mask | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.17 | 0.53 | 0.80 | 0.21 | 4.13 | 1.17 | 0.54 | 0.00 | 0.00 | 1.0 | 1842 |
| nexttoken-preamble +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.17 | 0.47 | 0.70 | 0.20 | 3.59 | 1.00 | 0.39 | 0.00 | 0.00 | 1.0 | 1836 |
| sampling +mask | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.20 | 0.37 | 0.44 | 0.15 | 5.74 | 1.22 | 0.42 | 0.00 | 0.00 | 10.0 | 19725 |
| sampling +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.15 | 0.31 | 0.36 | 0.15 | 6.27 | 1.24 | 0.49 | 0.00 | 0.00 | 10.0 | 19338 |
| verbalized +mask | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.18 | 0.33 | 0.45 | 0.14 | 4.74 | 1.10 | 0.26 | 0.00 | 0.00 | 1.0 | 6349 |
| verbalized +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.13 | 0.36 | 0.56 | 0.09 | 4.04 | 1.21 | 0.36 | 0.00 | 0.00 | 1.0 | 6266 |
| verbalized-mean +mask | hf:Qwen/Qwen2.5-7B-Instruct | 30 | 0.21 | 0.35 | 0.60 | 0.15 | 3.85 | 1.02 | 0.23 | 0.00 | 0.00 | 3.0 | 6349 |
| verbalized-mean +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 30 | 0.11 | 0.40 | 0.61 | 0.08 | 3.63 | 1.18 | 0.34 | 0.00 | 0.00 | 3.0 | 6266 |
| baseline | uniform-all | 30 | 0.01 | 0.03 | 0.05 | 0.01 | 4.62 | 0.99 | 0.00 | 0.83 | 0.00 | – | 0 |
| baseline | uniform-applicable | 30 | 0.10 | 0.29 | 0.48 | 0.10 | 2.57 | 0.90 | 0.00 | 0.00 | 0.00 | – | 0 |

## BlockWords

| estimator | model | points | top-1 | top-3 | top-5 | p(true) | NLL | Brier | ECE | invalid | ungrounded | calls/pt | tokens/pt |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| nexttoken | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.00 | 0.10 | 0.10 | 0.02 | 6.38 | 1.30 | 0.47 | 0.83 | 0.00 | 1.0 | 1858 |
| nexttoken | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.10 | 0.20 | 0.20 | 0.04 | 6.06 | 1.05 | 0.17 | 0.89 | 0.00 | 1.0 | 1847 |
| nexttoken-preamble | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.00 | 0.10 | 0.10 | 0.03 | 6.46 | 1.21 | 0.40 | 0.84 | 0.00 | 1.0 | 1868 |
| nexttoken-preamble | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.00 | 0.00 | 0.10 | 0.01 | 6.32 | 1.12 | 0.27 | 0.90 | 0.00 | 1.0 | 1857 |
| sampling | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.03 | 0.12 | 0.16 | 0.03 | 7.96 | 1.16 | 0.29 | 0.70 | 0.00 | 10.0 | 20052 |
| sampling | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.00 | 0.02 | 0.05 | 0.01 | 8.74 | 1.18 | 0.29 | 0.76 | 0.00 | 10.0 | 19565 |
| verbalized | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.03 | 0.15 | 0.15 | 0.03 | 7.79 | 1.19 | 0.32 | 0.78 | 0.00 | 1.0 | 6430 |
| verbalized | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 6.84 | 1.18 | 0.31 | 0.90 | 0.00 | 1.0 | 6325 |
| verbalized-mean | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.00 | 0.10 | 0.25 | 0.03 | 6.03 | 1.06 | 0.22 | 0.78 | 0.00 | 3.0 | 6430 |
| verbalized-mean | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 6.58 | 1.11 | 0.22 | 0.90 | 0.00 | 3.0 | 6325 |
| nexttoken +mask | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.10 | 0.40 | 0.90 | 0.13 | 4.30 | 1.32 | 0.56 | 0.00 | 0.00 | 1.0 | 1858 |
| nexttoken +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.20 | 0.50 | 0.90 | 0.21 | 4.19 | 1.11 | 0.48 | 0.00 | 0.00 | 1.0 | 1847 |
| nexttoken-preamble +mask | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.10 | 0.50 | 0.90 | 0.15 | 4.67 | 1.28 | 0.57 | 0.00 | 0.00 | 1.0 | 1868 |
| nexttoken-preamble +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.20 | 0.40 | 1.00 | 0.23 | 4.33 | 1.09 | 0.48 | 0.00 | 0.00 | 1.0 | 1857 |
| sampling +mask | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.14 | 0.32 | 0.40 | 0.12 | 6.24 | 1.41 | 0.56 | 0.00 | 0.00 | 10.0 | 20052 |
| sampling +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.04 | 0.19 | 0.30 | 0.06 | 7.12 | 1.55 | 0.66 | 0.00 | 0.00 | 10.0 | 19565 |
| verbalized +mask | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.17 | 0.44 | 0.65 | 0.16 | 4.35 | 1.14 | 0.36 | 0.00 | 0.00 | 1.0 | 6430 |
| verbalized +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.08 | 0.46 | 0.86 | 0.09 | 3.61 | 1.35 | 0.48 | 0.00 | 0.00 | 1.0 | 6325 |
| verbalized-mean +mask | hf:Qwen/Qwen2.5-7B-Instruct | 10 | 0.23 | 0.40 | 0.83 | 0.18 | 3.53 | 1.06 | 0.35 | 0.00 | 0.00 | 3.0 | 6430 |
| verbalized-mean +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 10 | 0.02 | 0.41 | 0.91 | 0.04 | 3.94 | 1.55 | 0.70 | 0.00 | 0.00 | 3.0 | 6325 |
| baseline | uniform-all | 10 | 0.01 | 0.02 | 0.04 | 0.01 | 4.85 | 0.99 | 0.00 | 0.96 | 0.00 | – | 0 |
| baseline | uniform-applicable | 10 | 0.19 | 0.57 | 0.93 | 0.19 | 1.67 | 0.81 | 0.00 | 0.00 | 0.00 | – | 0 |

## IntrusionDetection

| estimator | model | points | top-1 | top-3 | top-5 | p(true) | NLL | Brier | ECE | invalid | ungrounded | calls/pt | tokens/pt |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| nexttoken | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.15 | 0.40 | 0.65 | 0.16 | 4.24 | 1.24 | 0.52 | 0.10 | 0.00 | 1.0 | 1819 |
| nexttoken | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.10 | 0.20 | 0.25 | 0.04 | 4.61 | 1.12 | 0.34 | 0.35 | 0.00 | 1.0 | 1816 |
| nexttoken-preamble | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.10 | 0.50 | 0.60 | 0.16 | 4.23 | 1.25 | 0.60 | 0.11 | 0.00 | 1.0 | 1829 |
| nexttoken-preamble | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.05 | 0.40 | 0.40 | 0.12 | 3.71 | 1.03 | 0.35 | 0.31 | 0.00 | 1.0 | 1826 |
| sampling | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.18 | 0.32 | 0.41 | 0.11 | 5.73 | 1.09 | 0.24 | 0.26 | 0.06 | 10.0 | 19562 |
| sampling | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.20 | 0.37 | 0.38 | 0.12 | 5.99 | 1.01 | 0.24 | 0.32 | 0.01 | 10.0 | 19225 |
| verbalized | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.14 | 0.23 | 0.29 | 0.09 | 6.22 | 1.07 | 0.26 | 0.43 | 0.03 | 1.0 | 6309 |
| verbalized | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.07 | 0.24 | 0.31 | 0.06 | 5.14 | 1.08 | 0.24 | 0.44 | 0.02 | 1.0 | 6237 |
| verbalized-mean | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.20 | 0.21 | 0.33 | 0.09 | 4.85 | 0.97 | 0.20 | 0.43 | 0.03 | 3.0 | 6309 |
| verbalized-mean | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.15 | 0.25 | 0.45 | 0.06 | 4.13 | 0.97 | 0.04 | 0.44 | 0.02 | 3.0 | 6237 |
| nexttoken +mask | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.20 | 0.45 | 0.70 | 0.22 | 3.95 | 1.11 | 0.46 | 0.00 | 0.00 | 1.0 | 1819 |
| nexttoken +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.10 | 0.25 | 0.40 | 0.08 | 4.18 | 1.20 | 0.50 | 0.00 | 0.00 | 1.0 | 1816 |
| nexttoken-preamble +mask | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.20 | 0.55 | 0.75 | 0.25 | 3.86 | 1.12 | 0.52 | 0.00 | 0.00 | 1.0 | 1829 |
| nexttoken-preamble +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.15 | 0.50 | 0.55 | 0.19 | 3.22 | 0.95 | 0.34 | 0.00 | 0.00 | 1.0 | 1826 |
| sampling +mask | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.23 | 0.40 | 0.46 | 0.17 | 5.49 | 1.13 | 0.35 | 0.00 | 0.00 | 10.0 | 19562 |
| sampling +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.20 | 0.37 | 0.40 | 0.19 | 5.85 | 1.08 | 0.40 | 0.00 | 0.00 | 10.0 | 19225 |
| verbalized +mask | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.18 | 0.27 | 0.36 | 0.14 | 4.93 | 1.07 | 0.23 | 0.00 | 0.00 | 1.0 | 6309 |
| verbalized +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.15 | 0.31 | 0.41 | 0.09 | 4.26 | 1.14 | 0.30 | 0.00 | 0.00 | 1.0 | 6237 |
| verbalized-mean +mask | hf:Qwen/Qwen2.5-7B-Instruct | 20 | 0.20 | 0.33 | 0.48 | 0.14 | 4.01 | 1.01 | 0.23 | 0.00 | 0.00 | 3.0 | 6309 |
| verbalized-mean +mask | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20 | 0.15 | 0.40 | 0.46 | 0.10 | 3.48 | 0.99 | 0.15 | 0.00 | 0.00 | 3.0 | 6237 |
| baseline | uniform-all | 20 | 0.01 | 0.03 | 0.06 | 0.01 | 4.50 | 0.99 | 0.00 | 0.77 | 0.00 | – | 0 |
| baseline | uniform-applicable | 20 | 0.05 | 0.15 | 0.26 | 0.05 | 3.02 | 0.95 | 0.00 | 0.00 | 0.00 | – | 0 |

Next-token: share of the model's reply probability that falls on the grounded action strings at all, before renormalizing. For `nexttoken-preamble` this is given the preamble "I predict the agent's next action to be:" and pools `(name args)` with `name args`; *bare share* is the part of it written without parentheses, and *p(preamble)* is how likely the model was to write that exact preamble unprompted:

| estimator | model | grounded mass | bare share | p(preamble) |
|---|---|--:|--:|--:|
| nexttoken | hf:Qwen/Qwen2.5-7B-Instruct | 0.968 | – | – |
| nexttoken | hf:meta-llama/Meta-Llama-3-8B-Instruct | 0.235 | – | – |
| nexttoken-preamble | hf:Qwen/Qwen2.5-7B-Instruct | 0.995 | 0.000 | 0.0000 |
| nexttoken-preamble | hf:meta-llama/Meta-Llama-3-8B-Instruct | 0.952 | 0.005 | 0.0554 |
