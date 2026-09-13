#!/usr/bin/env python3
"""Regenerate every figure in this directory from results/.

    python3 make_figures.py

Requires matplotlib (pip install matplotlib). Reads only; writes fig2..fig4
as .pdf (for LaTeX) and .png (for eyeballing) into this directory.
The noise floor is a table in the paper, not a figure.
"""

import glob
import json
import os
import re
import statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, "..", "..", "results"))

BINARIES = ["timestamped", "claude", "codex"]
LABEL = {"timestamped": "baseline", "claude": "claude", "codex": "codex"}
COLOR = {"timestamped": "#2a78d6", "claude": "#eb6834", "codex": "#1baf7a"}

TOPOLOGIES = ["5000-sparse-deep", "5000-default", "5000-dense-shallow"]
NICE = {"5000-sparse-deep": "sparse-deep\n10 wide, 500 layers",
        "5000-default": "default\n100 wide, 50 layers",
        "5000-dense-shallow": "dense-shallow\n200 wide, 25 layers"}

PHASES = ["init", "rank", "mincross", "position", "splines"]
RAMP = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0f2f5e"]

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "figure.dpi": 150,
})


def end_to_end(topology):
    """-> {binary: [ms, ...]} pooled over every permutation."""
    pooled = defaultdict(list)
    for path in glob.glob(os.path.join(RESULTS, f"{topology}.gv-full-perm*.json")):
        for row in json.load(open(path))["results"]:
            b = re.search(r"binaries/(\w+)/", row["command"]).group(1)
            pooled[b] += [t * 1000 for t in row["times"]]
    return pooled


def phases(topology):
    """-> {binary: {phase: [ms, ...]}} from the timed runs only."""
    out = defaultdict(lambda: defaultdict(list))
    for path in glob.glob(os.path.join(RESULTS, "phases", f"{topology}.gv-*-perm*.txt")):
        b = re.search(r"-(timestamped|claude|codex)-perm", path).group(1)
        timed = False
        for line in open(path):
            line = line.strip()
            if line == "REAL START":
                timed = True
                continue
            if line == "REAL END":
                timed = False
                continue
            m = re.match(r"phase\t(\w+)\t([\d.]+)", line)
            if m and timed:
                out[b][m.group(1)].append(float(m.group(2)))
    return out


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.pdf / {name}.png")


E2E = {t: end_to_end(t) for t in TOPOLOGIES}
PH = {t: phases(t) for t in TOPOLOGIES}


# ---------------------------------------------------------------- fig 2
# Where baseline time goes, by topology. Shape moves the weights, not size.
fig, ax = plt.subplots(figsize=(7.4, 2.6))
for row, topo in enumerate(TOPOLOGIES):
    means = {p: st.mean(PH[topo]["timestamped"][p]) for p in PHASES}
    total = sum(means.values())
    left = 0.0
    for p, color in zip(PHASES, RAMP):
        w = means[p] / total * 100
        ax.barh(row, w, left=left, color=color, height=0.6,
                edgecolor="white", linewidth=1.5)
        if w > 7:
            ax.text(left + w / 2, row, f"{p}\n{w:.0f}%", ha="center", va="center",
                    fontsize=8, color="white" if color in RAMP[3:] else "#14181f")
        left += w
ax.set_yticks(range(len(TOPOLOGIES)))
ax.set_yticklabels([NICE[t] for t in TOPOLOGIES], fontsize=8)
ax.set_xlabel("share of baseline layout time (%)")
ax.set_xlim(0, 100)
ax.grid(False)
ax.set_title("Crossing minimization is 11% of the work on one shape and 64% on "
             "another,\nat identical node count", loc="left")
save(fig, "fig2_phase_composition")


# ---------------------------------------------------------------- fig 3
# End-to-end, all three topologies.
fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.9))
for ax, topo in zip(axes, TOPOLOGIES):
    base = st.mean(E2E[topo]["timestamped"])
    for i, b in enumerate(BINARIES):
        v = E2E[topo][b]
        ax.bar(i, st.mean(v), color=COLOR[b], width=0.62, zorder=1)
        ax.scatter([i] * len(v), v, s=5, color="#14181f", alpha=0.4,
                   linewidths=0, zorder=3)
        if b != "timestamped":
            ax.text(i, st.mean(v) * 0.5, f"{base/st.mean(v):.2f}x", ha="center",
                    color="white", fontsize=10, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels([LABEL[b] for b in BINARIES], fontsize=8)
    ax.set_title(NICE[topo].split("\n")[0])
axes[0].set_ylabel("layout time (ms)")
fig.tight_layout(rect=(0, 0, 1, 0.87))
fig.suptitle("End-to-end layout time (bars = mean of 30 runs; dots = individual runs)",
             y=0.99)
save(fig, "fig3_end_to_end")


# ---------------------------------------------------------------- fig 4
# Per-phase speedup. Claude wins four phases; Codex wins one.
fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.9), sharey=True)
width = 0.36
for ax, topo in zip(axes, TOPOLOGIES):
    for k, b in enumerate(["claude", "codex"]):
        xs, ys = [], []
        for i, p in enumerate(PHASES):
            xs.append(i + (k - 0.5) * width)
            ys.append(st.mean(PH[topo]["timestamped"][p]) / st.mean(PH[topo][b][p]))
        ax.bar(xs, ys, width=width, color=COLOR[b], label=LABEL[b], zorder=2)
    ax.axhline(1.0, color="#14181f", lw=1, ls="--", zorder=3)
    ax.set_xticks(range(len(PHASES)))
    ax.set_xticklabels(PHASES, rotation=45, ha="right", fontsize=8)
    ax.set_title(NICE[topo].split("\n")[0])
axes[0].set_ylabel("speedup over baseline")
axes[0].legend(frameon=False, fontsize=8, loc="upper left")
fig.tight_layout(rect=(0, 0, 1, 0.87))
fig.suptitle("Per-phase speedup. Claude improves three phases; Codex improves one.",
             y=0.99)
save(fig, "fig4_phase_speedup")

print("\ndone.")
