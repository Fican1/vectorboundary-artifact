#!/usr/bin/env python3
"""VectorBoundary Fig. 1: dynamic instructions per token, schedule x VLEN.

Style follows Peccia ICCAD'25 Fig. 5 (instruction-count bars, hatched
baseline, serif fonts); data unchanged from v2.
"""
import matplotlib.pyplot as plt

import pubstyle
from pubstyle import COLW, SCHED_STYLE, SCHED_LABEL

SERIES = ["norepack", "q4_0_8x1", "q4_0_16x1", "q4_0_32x1", "q4_0_64x1", "q4_0_8x8"]

decode = {
    128:  {"norepack": 116.4, "q4_0_8x1": 109.3, "q4_0_8x8": 74.6},
    256:  {"norepack": 115.8, "q4_0_8x1": 89.9, "q4_0_16x1": 57.7, "q4_0_8x8": 49.9},
    512:  {"norepack": 115.5, "q4_0_8x1": 80.2, "q4_0_16x1": 48.0, "q4_0_32x1": 31.9},
    1024: {"norepack": 115.4, "q4_0_8x1": 75.4, "q4_0_16x1": 43.2, "q4_0_32x1": 27.1, "q4_0_64x1": 19.0},
}
prefill = {
    128:  {"norepack": 93.5, "q4_0_8x1": 60.6, "q4_0_8x8": 26.1},
    256:  {"norepack": 92.7, "q4_0_8x1": 59.9, "q4_0_16x1": 35.7, "q4_0_8x8": 21.3},
    512:  {"norepack": 92.3, "q4_0_8x1": 59.5, "q4_0_16x1": 35.4, "q4_0_32x1": 21.8},
    1024: {"norepack": 92.2, "q4_0_8x1": 59.3, "q4_0_16x1": 35.2, "q4_0_32x1": 21.6, "q4_0_64x1": 16.4},
}

pubstyle.setup()
fig, axes = plt.subplots(1, 2, figsize=(COLW, 1.8), sharey=True)
vlens = [128, 256, 512, 1024]
bw, gap = 0.14, 0.008

for ax, data, panel in [(axes[0], decode, "Decode"), (axes[1], prefill, "Prefill")]:
    for gi, v in enumerate(vlens):
        vals = data[v]
        best = min(vals, key=vals.get)
        for si, s in enumerate(SERIES):
            if s not in vals:
                continue
            st = SCHED_STYLE[s]
            x = gi + (si - (len(SERIES) - 1) / 2) * (bw + gap)
            ax.bar(x, vals[s], width=bw, color=st["color"], hatch=st["hatch"],
                   edgecolor="black", linewidth=0.3, zorder=3)
            if s == best:
                ax.text(x, vals[s] + 2.5, f"{vals[s]:.0f}", ha="center",
                        va="bottom", fontsize=5.5, rotation=0)
    ax.set_title(panel, fontsize=8, pad=2)
    ax.set_xticks(range(len(vlens)))
    ax.set_xticklabels([str(v) for v in vlens])
    ax.set_xlabel("VLEN (bits)", labelpad=1)
    ax.set_ylim(0, 128)

axes[0].set_ylabel("Instr. / token (M)")
handles = [plt.matplotlib.patches.Patch(
    facecolor=SCHED_STYLE[s]["color"], hatch=SCHED_STYLE[s]["hatch"],
    edgecolor="black", linewidth=0.3, label=SCHED_LABEL[s]) for s in SERIES]
fig.legend(handles=handles, loc="upper center", ncol=6,
           bbox_to_anchor=(0.5, 1.10), columnspacing=0.9, handlelength=1.1,
           handletextpad=0.4)
fig.subplots_adjust(wspace=0.08)
pubstyle.finish(fig, list(axes), "insn-comparison")
