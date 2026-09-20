#!/usr/bin/env python3
"""VectorBoundary Fig. 7: L1D misses/token invariant to schedule and cache size."""
import matplotlib.pyplot as plt

import pubstyle
from pubstyle import COLW, SCHED_STYLE, SCHED_LABEL

SERIES = ["norepack", "q4_0_8x1", "q4_0_16x1", "q4_0_8x8"]
data = {
    "32K L1D / 512K L2":  {"norepack": 1.531, "q4_0_8x1": 1.511, "q4_0_16x1": 1.511, "q4_0_8x8": 1.511},
    "128K L1D / 2M L2":   {"norepack": 1.497, "q4_0_8x1": 1.499, "q4_0_16x1": 1.499, "q4_0_8x8": 1.499},
}
configs = list(data.keys())

pubstyle.setup()
fig, ax = plt.subplots(figsize=(COLW, 1.45))
bw = 0.19
for si, s in enumerate(SERIES):
    st = SCHED_STYLE[s]
    xs = [gi + (si - 1.5) * bw for gi in range(len(configs))]
    ys = [data[c][s] for c in configs]
    ax.bar(xs, ys, width=bw, color=st["color"], hatch=st["hatch"],
           edgecolor="black", linewidth=0.3, label=SCHED_LABEL[s], zorder=3)

ax.set_xticks(range(len(configs)))
ax.set_xticklabels(configs)
ax.set_ylabel("L1D misses / token (M)")
ax.set_ylim(0, 1.9)
ax.legend(loc="upper center", ncol=4, columnspacing=0.9, handlelength=1.1,
          handletextpad=0.4)
pubstyle.finish(fig, ax, "cache-invariance")
