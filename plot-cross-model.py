#!/usr/bin/env python3
"""VectorBoundary Fig. 5: cross-model oracle-gap of the upstream rule.

Encoding (colorblind-safe, survives grayscale): filled bars fall short
of the oracle, open bars match it exactly; dagger = true oracle is to
leave the tensor unrepacked. Update the LaTeX caption if this changes.
"""
import matplotlib.pyplot as plt

import pubstyle
from pubstyle import COLW, BLUE, GRAY

rows = [
    ("Qwen2.5-0.5B Q4_0 dec",   0.879),
    ("Qwen2.5-0.5B Q4_0 pre",   0.647),
    ("Qwen3-0.6B Q4_0 dec",     0.876),
    ("Qwen3-0.6B Q4_0 pre",     0.636),
    ("Qwen3-0.6B Q8_0 dec†", 0.952),
    ("Qwen3-0.6B Q8_0 pre",     1.000),
    ("SmolLM2-135M Q4_0 dec",   0.865),
    ("SmolLM2-135M Q4_0 pre",   0.596),
    ("SmolLM2-135M Q4_K_M dec", 1.000),
    ("SmolLM2-135M Q4_K_M pre", 1.000),
    ("SmolLM2-135M Q8_0 dec†", 0.993),
    ("SmolLM2-135M Q8_0 pre",   1.000),
    ("SmolLM2-360M Q4_0 dec",   0.837),
    ("SmolLM2-360M Q4_0 pre",   0.632),
]
labels = [r[0] for r in rows]
scores = [r[1] for r in rows]

pubstyle.setup()
fig, ax = plt.subplots(figsize=(COLW, 2.3))
y = range(len(labels))
for i, s in enumerate(scores):
    if s >= 0.9995:
        ax.barh(i, s, color="white", edgecolor=BLUE, linewidth=0.7,
                zorder=3, height=0.62)
    else:
        ax.barh(i, s, color=BLUE, edgecolor="black", linewidth=0.3,
                zorder=3, height=0.62)
    ax.text(s + 0.015, i, f"{s:.2f}", va="center", fontsize=6)
ax.axvline(1.0, color=GRAY, linewidth=0.6, linestyle="--", zorder=1)
ax.set_yticks(list(y))
ax.set_yticklabels(labels, fontsize=6)
ax.invert_yaxis()
ax.set_xlim(0, 1.12)
ax.set_xlabel("Oracle-normalized score (1.0 = optimal)")
pubstyle.finish(fig, ax, "cross-model", grid_axis="x")
