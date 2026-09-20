#!/usr/bin/env python3
"""VectorBoundary Fig. 4: oracle-normalized score by policy (main result)."""
import matplotlib.pyplot as plt

import pubstyle
from pubstyle import COLW, BLUE, GRAY

policies = ["Random", "Upstream\n(VLEN-matched)", "Widest-legal\nheuristic", "VectorBoundary"]
mean_score = [0.613, 0.744, 0.762, 1.000]
min_score  = [0.370, 0.178, 0.178, 1.000]

pubstyle.setup()
fig, ax = plt.subplots(figsize=(COLW, 1.75))
bw = 0.34
x = range(len(policies))
ax.bar([i - bw / 2 for i in x], mean_score, width=bw, color=BLUE,
       edgecolor="black", linewidth=0.3, zorder=3, label="mean")
ax.bar([i + bw / 2 for i in x], min_score, width=bw, color="white", hatch="////",
       edgecolor=GRAY, linewidth=0.5, zorder=3, label="worst case")

for i, (m, mn) in enumerate(zip(mean_score, min_score)):
    ax.text(i - bw / 2, m + 0.02, f"{m:.2f}", ha="center", fontsize=6)
    ax.text(i + bw / 2, mn + 0.02, f"{mn:.2f}", ha="center", fontsize=6)

ax.set_xticks(list(x))
ax.set_xticklabels(policies)
ax.set_ylabel("Score (1.0 = optimal)")
ax.set_ylim(0, 1.12)
ax.axhline(1.0, color=GRAY, linewidth=0.6, linestyle="--", zorder=1)
ax.legend(loc="upper left", ncol=1, handlelength=1.2)
pubstyle.finish(fig, ax, "main-comparison")
