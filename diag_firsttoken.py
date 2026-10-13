#!/usr/bin/env python3
"""Diagnostic: how does an open model begin its reply to the nexttoken prompt?

For a few decision points, prints the top first tokens, the first-token mass
that starts with "(", the greedy reply and a few sampled replies. Uses the same
prompt and chat rendering as `nextaction.py run --estimator nexttoken`.

  python diag_firsttoken.py Qwen/Qwen2.5-7B-Instruct meta-llama/Meta-Llama-3-8B-Instruct
"""

import argparse
import json

import torch

import nextaction as N

POINTS = [("blockwords", 0), ("blockwords", 3), ("blockwords", 6), ("intrusion", 0), ("intrusion", 10)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("models", nargs="+")
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--out", default="results/nextaction/diag_firsttoken.jsonl")
    args = ap.parse_args()
    worlds = {n: N.World(n) for n in {n for n, _ in POINTS}}
    out = open(args.out, "w")
    for name in args.models:
        m = N.HFModel(name, dtype="bfloat16")
        tok = m.tok
        vocab = [tok.decode([i]) for i in range(len(tok))]
        for n, t in POINTS:
            w = worlds[n]
            system, user = N.build_prompt(w, t, "nexttoken", 5)
            text = m.render(system, user)
            ids = torch.tensor([m.encode(text)], device=m.device)
            with torch.no_grad():
                lp = m.model(ids).logits[0, -1].float().log_softmax(-1)
            p = lp.exp()
            top = torch.topk(p, 15)
            paren = sum(p[i].item() for i, s in enumerate(vocab[:p.shape[0]]) if s.lstrip().startswith("("))
            with torch.no_grad():
                g = m.model.generate(ids, attention_mask=torch.ones_like(ids), do_sample=False,
                                     max_new_tokens=40, pad_token_id=tok.eos_token_id)
            greedy = tok.decode(g[0, ids.shape[1]:], skip_special_tokens=True)
            samples = [m.generate(system, user, 1.0, 40, seed)["content"] for seed in range(args.samples)]
            rec = {"model": name, "domain": n, "t": t, "target": w.plan[t],
                   "first_token_paren_mass": paren,
                   "top_first_tokens": [(vocab[i], round(v, 4)) for v, i in zip(top.values.tolist(), top.indices.tolist())],
                   "greedy": greedy, "samples": samples}
            out.write(json.dumps(rec) + "\n")
            out.flush()
            print(f"\n=== {name} | {n} t={t} | target {w.plan[t]}")
            print(f"first-token mass starting with '(': {paren:.3f}")
            print("top first tokens:", ", ".join(f"{s!r} {v:.3f}" for s, v in rec["top_first_tokens"]))
            print("greedy :", repr(greedy))
            for s in samples:
                print("sample :", repr(s))
        del m
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
