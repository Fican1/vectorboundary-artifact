#!/usr/bin/env python3
"""VectorBoundary: selection-quality evaluation on real measured data.

Task: within each context (model, quant, vlen, batch, stage), rank candidate
schedules by predicted cost. Score = TLP-style oracle-normalized top-k:
    score(policy) = oracle_cost / cost(policy pick)   (1.0 = perfect)
Predictor: ridge regression on log(insn/token) with white-box features,
evaluated leave-one-context-out (the model never sees the test context).
Baselines: upstream VLEN-matched rule, widest-legal heuristic, random.
"""
import csv
import math
import os
import random
from collections import defaultdict

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_BYTES = {  # gguf file sizes as weight-stream proxy
    ("SmolLM2-135M", "Q4_0"): 91893088,
    ("SmolLM2-135M", "Q8_0"): 144811360,
    ("SmolLM2-135M", "Q4_K_M"): 105454432,
    ("SmolLM2-360M", "Q4_0"): 229733280,
    ("Qwen2.5-0.5B", "Q4_0"): 352972352,
    ("Qwen3-0.6B", "Q4_0"): 469671328,
    ("Qwen3-0.6B", "Q8_0"): 804753824,
}

def sched_family(s):
    if s == "norepack":
        return "norepack"
    if s.endswith("8x8"):
        return "8x8"
    return "Nx1"

def sched_m(s):
    if s == "norepack":
        return 0
    return int(s.split("_")[-1].split("x")[0])

rows = list(csv.DictReader(open(os.path.join(BASE, "dataset.csv"), encoding="utf-8")))
for r in rows:
    r["vlen"] = int(r["vlen"]); r["batch"] = int(r["batch"])
    r["cost"] = float(r["insns_total_per_tok"])

ctxs = defaultdict(list)
for r in rows:
    ctxs[(r["model"], r["quant"], r["vlen"], r["batch"], r["stage"])].append(r)

def feats(r):
    fam = sched_family(r["schedule"])
    m = sched_m(r["schedule"])
    vlenb = r["vlen"] // 8
    util = (2 * m) / vlenb if m else 0.0   # width utilization of Nx1 bound
    dec = 1.0 if r["stage"] == "decode" else 0.0
    gemm = 1.0 if (r["stage"] == "prefill" or r["batch"] >= 4) else 0.0
    logb = math.log(MODEL_BYTES[(r["model"], r["quant"])])
    return [
        1.0,
        1.0 if fam == "norepack" else 0.0,
        1.0 if fam == "8x8" else 0.0,
        math.log(m + 1),
        util,
        dec,
        gemm,
        dec * (1.0 if fam == "norepack" else 0.0),
        gemm * math.log(m + 1),
        gemm * (1.0 if fam == "8x8" else 0.0),
        logb,
        1.0 if r["quant"].startswith("Q8") else 0.0,
        1.0 if r["quant"].startswith("Q4_K") else 0.0,
    ]

def upstream_rule(cands, vlen):
    vlenb = vlen // 8
    m = vlenb // 2
    for r in cands:
        if sched_family(r["schedule"]) == "Nx1" and sched_m(r["schedule"]) == m:
            return r
    for r in cands:
        if sched_family(r["schedule"]) == "8x8":
            return r
    return next(r for r in cands if r["schedule"] == "norepack")

def widest_legal(cands):
    best = max(cands, key=lambda r: sched_m(r["schedule"]))
    return best

def score(pick, cands, k=1):
    oracle = min(r["cost"] for r in cands)
    return oracle / pick["cost"]

keys = sorted(ctxs.keys())
results = defaultdict(list)
rng = random.Random(42)

for test_key in keys:
    test = ctxs[test_key]
    train = [r for k in keys if k != test_key for r in ctxs[k]]
    X = np.array([feats(r) for r in train])
    y = np.array([math.log(r["cost"]) for r in train])
    lam = 1e-3
    w = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ y)
    preds = [(float(np.array(feats(r)) @ w), r) for r in test]
    preds.sort(key=lambda t: t[0])
    ranked = [r for _, r in preds]
    oracle = min(r["cost"] for r in test)

    results["ours_top1"].append(oracle / ranked[0]["cost"])
    results["ours_top2"].append(oracle / min(r["cost"] for r in ranked[:2]))
    results["upstream"].append(oracle / upstream_rule(test, test_key[2])["cost"])
    results["widest"].append(oracle / widest_legal(test)["cost"])
    results["random"].append(sum(oracle / r["cost"] for r in test) / len(test))

print(f"contexts: {len(keys)}  (score = oracle-normalized cost, 1.0 = always optimal)\n")
print(f"{'policy':>28} {'mean score':>11} {'min score':>10} {'top1 hit%':>10}")
for name, label in [("ours_top1", "ours (LOOCV ridge) top-1"),
                    ("ours_top2", "ours top-2"),
                    ("upstream", "upstream VLEN rule"),
                    ("widest", "widest-legal heuristic"),
                    ("random", "random expectation")]:
    v = results[name]
    hit = sum(1 for s in v if s > 0.999) / len(v) * 100
    print(f"{label:>28} {sum(v)/len(v):>11.3f} {min(v):>10.3f} {hit:>9.0f}%")

print("\nper-context detail (ours top-1 vs upstream):")
for k, o, u in zip(keys, results["ours_top1"], results["upstream"]):
    flag = "  <-- ours wins" if o > u + 1e-9 else ("  <-- upstream wins" if u > o + 1e-9 else "")
    print(f"  {str(k):>55} ours={o:.3f} upstream={u:.3f}{flag}")
