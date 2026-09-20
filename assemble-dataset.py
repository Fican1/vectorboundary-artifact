#!/usr/bin/env python3
"""VectorBoundary: assemble all insn sweep CSVs into one tidy selection dataset.

Each output row = one (context, schedule) pair with per-token costs.
Context = (model, quant, vlen, stage[, batch]). Written to dataset.csv.
"""
import csv
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
METRICS = ["insns_total", "v_arith", "vsetvl", "v_load", "v_store"]

SOURCES = [
    # (file, model, quant)
    ("insn-qemu-clean.csv",  "SmolLM2-135M", "Q4_0"),
    ("insn-qwen05b-q40.csv", "Qwen2.5-0.5B", "Q4_0"),
    ("insn-360m-q40.csv",    "SmolLM2-360M", "Q4_0"),
    ("insn-135m-q80.csv",    "SmolLM2-135M", "Q8_0"),
    ("insn-135m-q4km.csv",   "SmolLM2-135M", "Q4_K_M"),
    ("insn-qwen3-06b-q40.csv", "Qwen3-0.6B", "Q4_0"),
    ("insn-qwen3-06b-q80.csv", "Qwen3-0.6B", "Q8_0"),
]

rows = []
for fname, model, quant in SOURCES:
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        continue
    runs = defaultdict(dict)
    for r in csv.DictReader(open(path, encoding="utf-8")):
        runs[(int(r["vlen"]), r["schedule"])][r["run"]] = r
    for (vlen, sched), rr in sorted(runs.items()):
        if not all(t in rr for t in "ABC"):
            continue
        A, B, C = rr["A"], rr["B"], rr["C"]
        try:
            dgen = int(B["n_gen"]) - int(A["n_gen"])
            dpp = int(C["n_prompt"]) - int(A["n_prompt"])
        except ValueError:
            continue
        for stage, hi, lo, denom in [("decode", B, A, dgen), ("prefill", C, A, dpp)]:
            row = {"model": model, "quant": quant, "vlen": vlen, "batch": 1,
                   "stage": stage, "schedule": sched}
            for m in METRICS:
                row[m + "_per_tok"] = (int(hi[m]) - int(lo[m])) / denom
            rows.append(row)

# batch sweep: decode at batch 1/2/4/8 (SmolLM2-135M Q4_0, vlen 256)
bruns = defaultdict(dict)
bpath = os.path.join(BASE, "batch-qemu.csv")
if os.path.exists(bpath):
    for r in csv.DictReader(open(bpath, encoding="utf-8")):
        bruns[(r["schedule"], int(r["npl"]))][int(r["ntg"])] = r
    for (sched, npl), rr in sorted(bruns.items()):
        if 1 in rr and 9 in rr:
            n = npl * 8
            row = {"model": "SmolLM2-135M", "quant": "Q4_0", "vlen": 256,
                   "batch": npl, "stage": "decode", "schedule": sched}
            for m in METRICS:
                row[m + "_per_tok"] = (int(rr[9][m]) - int(rr[1][m])) / n
            if npl > 1:
                rows.append(row)

out = os.path.join(BASE, "dataset.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

ctx = defaultdict(list)
for r in rows:
    ctx[(r["model"], r["quant"], r["vlen"], r["batch"], r["stage"])].append(r["schedule"])
print(f"rows: {len(rows)}, contexts: {len(ctx)}")
for k, v in sorted(ctx.items()):
    print(f"  {k}: {len(v)} schedules")
