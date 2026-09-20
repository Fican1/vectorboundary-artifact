"""Shared publication style for VectorBoundary paper figures.

Conventions extracted from the DAC/ICCAD comparison papers
(Pelke DAC'25, Peccia ICCAD'25; see paper-dac/STYLE-GUIDE.md):
serif fonts matching the paper body, figures sized 1:1 to the acmart
single column (3.335 in) so no downscaling happens, muted
colorblind-safe palette (Okabe-Ito), hatching on bars so figures
survive grayscale printing, no in-figure titles (captions carry that),
baseline series drawn in gray.
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# acmart sigconf \linewidth in inches (single column)
COLW = 3.335

# Okabe-Ito, reordered: baseline gray first is NOT here; use GRAY for baselines.
BLUE = "#0072B2"
VERMILLION = "#D55E00"
GREEN = "#009E73"
ORANGE = "#E69F00"
PURPLE = "#CC79A7"
SKY = "#56B4E9"
GRAY = "#7F7F7F"
DARK = "#2B2B2B"

# schedule series -> stable color + hatch across every figure
SCHED_STYLE = {
    "norepack":   dict(color=GRAY,       hatch="////"),
    "q4_0_8x1":   dict(color=ORANGE,     hatch=""),
    "q4_0_16x1":  dict(color=BLUE,       hatch=""),
    "q4_0_32x1":  dict(color=SKY,        hatch=""),
    "q4_0_64x1":  dict(color=PURPLE,     hatch=""),
    "q4_0_8x8":   dict(color=GREEN,      hatch=""),
}
SCHED_LABEL = {
    "norepack": "no repack", "q4_0_8x1": "8x1", "q4_0_16x1": "16x1",
    "q4_0_32x1": "32x1", "q4_0_64x1": "64x1", "q4_0_8x8": "8x8",
}

FIGDIR = Path(__file__).resolve().parents[1] / "paper-dac" / "fig"


def setup():
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.0,
        "ytick.major.size": 2.0,
        "grid.color": "#CCCCCC",
        "grid.linewidth": 0.5,
        "hatch.linewidth": 0.5,
        "lines.linewidth": 1.2,
        "lines.markersize": 3.5,
        "legend.frameon": False,
        "figure.dpi": 200,
        "savefig.dpi": 300,
        "pdf.fonttype": 42,   # embed TrueType, keeps text selectable
    })


def finish(fig, ax_or_axes, name, grid_axis="y"):
    """Common spine/grid treatment + save PDF and PNG into paper-dac/fig."""
    axes = ax_or_axes if isinstance(ax_or_axes, (list, tuple)) else [ax_or_axes]
    for ax in axes:
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        if grid_axis:
            ax.grid(axis=grid_axis, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(length=2.0)
    fig.savefig(FIGDIR / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(FIGDIR / f"{name}.png", bbox_inches="tight", pad_inches=0.02)
    print(f"saved {FIGDIR / name}.pdf/.png")
