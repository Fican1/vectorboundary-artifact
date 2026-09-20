#!/usr/bin/env python3
"""VectorBoundary Fig. 6: 8x8-vs-16x1 advantage vs. matrix size (VLEN=256)."""
import matplotlib.pyplot as plt

import pubstyle
from pubstyle import COLW, BLUE, VERMILLION, GRAY

sizes = [32, 64, 128, 256, 512]
ratio_prefill = [5.608, 4.838, 3.439, 2.537, 2.048]   # M=N (prefill-like)
ratio_decode  = [1.011, 1.063, 1.169, 1.259, 1.302]   # M=1 (decode-like)

pubstyle.setup()
fig, ax = plt.subplots(figsize=(COLW, 1.6))
ax.plot(range(len(sizes)), ratio_prefill, marker="o", color=BLUE,
        label="$M{=}N$ (prefill-like)", zorder=3)
ax.plot(range(len(sizes)), ratio_decode, marker="s", color=VERMILLION,
        label="$M{=}1$ (decode-like)", zorder=3)
ax.axhline(1.0, color=GRAY, linewidth=0.6, linestyle="--", zorder=1)

ax.set_xticks(range(len(sizes)))
ax.set_xticklabels([f"${s}^2$" for s in sizes])
ax.set_xlabel("matrix size $N{=}K$", labelpad=1)
ax.set_ylabel("insn(16x1) / insn(8x8)")
ax.set_ylim(0.8, 6.0)
ax.legend(loc="upper right", handlelength=1.4)
pubstyle.finish(fig, ax, "shape-boundary")
