#!/usr/bin/env python3
"""VectorBoundary Tier-1 analysis: differential instruction counts per token.

Reads insn-qemu.csv (runs A/B/C per config), computes:
  decode per-token  = (B - A) / (n_gen_B - n_gen_A)
  prefill per-token = (C - A) / (n_prompt_C - n_prompt_A)
Emits insn-per-token.csv and a markdown summary.
"""
import csv
import sys
from collections import defaultdict

SRC = sys.argv[1] if len(sys.argv) > 1 else "insn-qemu.csv"
METRICS = ["insns_total", "v_arith", "vsetvl", "v_load", "v_store"]

rows = defaultdict(dict)
with open(SRC, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        key = (int(r["vlen"]), r["schedule"])
        rows[key][r["run"]] = r

out = []
for (vlen, sched), runs in sorted(rows.items()):
    if not all(t in runs for t in "ABC"):
        print(f"skip {vlen}/{sched}: incomplete runs {sorted(runs)}", file=sys.stderr)
        continue
    A, B, C = runs["A"], runs["B"], runs["C"]
    dgen = int(B["n_gen"]) - int(A["n_gen"])
    dpp = int(C["n_prompt"]) - int(A["n_prompt"])
    rec = {"vlen": vlen, "schedule": sched, "dec_tokens": dgen, "pp_tokens": dpp}
    for m in METRICS:
        rec[f"dec_{m}"] = (int(B[m]) - int(A[m])) / dgen
        rec[f"pp_{m}"] = (int(C[m]) - int(A[m])) / dpp
    out.append(rec)

with open("insn-per-token.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

def fmt(v, scale=1e6):
    return f"{v/scale:.2f}"

base = {r["vlen"]: r for r in out if r["schedule"] == "norepack"}
print("\n## Decode: M instructions per generated token (lower is better)\n")
print("| vlen | schedule | total | v_arith | vsetvl | v_load | v_store | vs norepack |")
print("|---|---|---:|---:|---:|---:|---:|---:|")
for r in out:
    b = base.get(r["vlen"])
    ratio = f'{b["dec_insns_total"]/r["dec_insns_total"]:.2f}x' if b else "-"
    print(f'| {r["vlen"]} | {r["schedule"]} | {fmt(r["dec_insns_total"])} | {fmt(r["dec_v_arith"])} '
          f'| {fmt(r["dec_vsetvl"])} | {fmt(r["dec_v_load"])} | {fmt(r["dec_v_store"])} | {ratio} |')

print("\n## Prefill: M instructions per prompt token (lower is better)\n")
print("| vlen | schedule | total | v_arith | vsetvl | v_load | v_store | vs norepack |")
print("|---|---|---:|---:|---:|---:|---:|---:|")
for r in out:
    b = base.get(r["vlen"])
    ratio = f'{b["pp_insns_total"]/r["pp_insns_total"]:.2f}x' if b else "-"
    print(f'| {r["vlen"]} | {r["schedule"]} | {fmt(r["pp_insns_total"])} | {fmt(r["pp_v_arith"])} '
          f'| {fmt(r["pp_vsetvl"])} | {fmt(r["pp_v_load"])} | {fmt(r["pp_v_store"])} | {ratio} |')
