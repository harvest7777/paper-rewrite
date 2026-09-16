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

BINARIES = ["timestamped",
            "claude", "claude_2", "claude_parallel", "claude_parallel_2",
            "codex", "codex_2", "codex_parallel", "codex_parallel_2"]
AGENTS = [b for b in BINARIES if b != "timestamped"]


def _label(b):
    if b == "timestamped":
        return "baseline"
    return b.replace("_parallel", " par").replace("_2", " 2")


LABEL = {b: _label(b) for b in BINARIES}
COLOR = {"timestamped": "#2a78d6",
         "claude": "#eb6834", "claude_2": "#f59b6b",
         "claude_parallel": "#c14a1c", "claude_parallel_2": "#8a3411",
         "codex": "#1baf7a", "codex_2": "#63cfa4",
         "codex_parallel": "#0f7d55", "codex_parallel_2": "#0a5a3c"}

# Longest first, so claude_parallel_2 never matches as claude.
BIN_RE = re.compile(r"-(" + "|".join(sorted(BINARIES, key=len, reverse=True))
                    + r")-perm")

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
        m = BIN_RE.search(path)
        if not m:
            continue
        b = m.group(1)
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
mincross_shares = []
for topo in TOPOLOGIES:
    means = {p: st.mean(PH[topo]["timestamped"][p]) for p in PHASES}
    mincross_shares.append(means["mincross"] / sum(means.values()) * 100)
ax.set_title(f"Crossing minimization is {min(mincross_shares):.0f}% of the work on one "
             f"shape and {max(mincross_shares):.0f}% on another,\nat identical node count",
             loc="left")
save(fig, "fig2_phase_composition")


# ---------------------------------------------------------------- fig 3
# End-to-end, all three topologies.
fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.4))
runs_per_bar = 0
for ax, topo in zip(axes, TOPOLOGIES):
    present = [b for b in BINARIES if E2E[topo].get(b)]
    base = st.mean(E2E[topo]["timestamped"]) if E2E[topo].get("timestamped") else None
    for i, b in enumerate(present):
        v = E2E[topo][b]
        runs_per_bar = max(runs_per_bar, len(v))
        ax.bar(i, st.mean(v), color=COLOR[b], width=0.62, zorder=1)
        ax.scatter([i] * len(v), v, s=5, color="#14181f", alpha=0.4,
                   linewidths=0, zorder=3)
        if base and b != "timestamped":
            ax.text(i, st.mean(v) * 0.5, f"{base/st.mean(v):.2f}x", ha="center",
                    color="white", fontsize=8, fontweight="bold", rotation=90)
    ax.set_xticks(range(len(present)))
    ax.set_xticklabels([LABEL[b] for b in present], fontsize=7,
                       rotation=45, ha="right")
    ax.set_title(NICE[topo].split("\n")[0])
axes[0].set_ylabel("layout time (ms)")
fig.tight_layout(rect=(0, 0, 1, 0.87))
fig.suptitle(f"End-to-end layout time (bars = mean of {runs_per_bar} runs; "
             "dots = individual runs)", y=0.99)
save(fig, "fig3_end_to_end")


# ---------------------------------------------------------------- fig 4
# Per-phase speedup. Claude wins four phases; Codex wins one.
fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.4), sharey=True)
for ax, topo in zip(axes, TOPOLOGIES):
    base = PH[topo].get("timestamped")
    present = [b for b in AGENTS if PH[topo].get(b)] if base else []
    width = 0.8 / max(len(present), 1)
    for k, b in enumerate(present):
        xs, ys = [], []
        for i, p in enumerate(PHASES):
            if not base.get(p) or not PH[topo][b].get(p):
                continue
            xs.append(i + (k - (len(present) - 1) / 2) * width)
            ys.append(st.mean(base[p]) / st.mean(PH[topo][b][p]))
        ax.bar(xs, ys, width=width, color=COLOR[b], label=LABEL[b], zorder=2)
    ax.axhline(1.0, color="#14181f", lw=1, ls="--", zorder=3)
    ax.set_xticks(range(len(PHASES)))
    ax.set_xticklabels(PHASES, rotation=45, ha="right", fontsize=8)
    ax.set_title(NICE[topo].split("\n")[0])
axes[0].set_ylabel("speedup over baseline")
axes[0].legend(frameon=False, fontsize=7, loc="upper left", ncol=2)
fig.tight_layout(rect=(0, 0, 1, 0.87))
fig.suptitle("Per-phase speedup over baseline, by binary.", y=0.99)
save(fig, "fig4_phase_speedup")

# ---------------------------------------------------------------- fig 5
# What the threads actually buy. Same binaries at one thread and at their own
# default; the gap between the pair is the part concurrency accounts for.
PARALLEL = ["claude_parallel", "claude_parallel_2"]
SERIAL_TONE = "#c3ccd8"


def thread_scaling(topology):
    """-> {binary: {"1": [ms, ...], "def": [ms, ...]}} from thread-scaling/."""
    pooled = defaultdict(lambda: defaultdict(list))
    pattern = os.path.join(RESULTS, "thread-scaling",
                           f"{topology}.gv-threads-perm*.json")
    for path in glob.glob(pattern):
        for row in json.load(open(path))["results"]:
            m = re.search(r"binaries/([^/]+)/", row["command"])
            if not m:
                continue
            key = "1" if "GV_THREADS=1" in row["command"] else "def"
            pooled[m.group(1)][key] += [t * 1000 for t in row["times"]]
    return pooled


TS = {t: thread_scaling(t) for t in TOPOLOGIES}

if all(TS[t].get("timestamped") for t in TOPOLOGIES):
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 3.0), sharey=True)
    width = 0.34
    for ax, topo in zip(axes, TOPOLOGIES):
        base = st.mean(TS[topo]["timestamped"]["def"])
        for k, b in enumerate(PARALLEL):
            one = base / st.mean(TS[topo][b]["1"])
            dflt = base / st.mean(TS[topo][b]["def"])
            ax.bar(k - width / 2, one, width=width, color=SERIAL_TONE,
                   zorder=2, label="1 thread" if k == 0 else None)
            ax.bar(k + width / 2, dflt, width=width, color=COLOR[b], zorder=2,
                   label="default threads" if k == 0 else None)
            ax.text(k, max(one, dflt) + 0.08, f"{dflt / one:.2f}$\\times$",
                    ha="center", fontsize=8, fontweight="bold")
        ax.axhline(1.0, color="#14181f", lw=1, ls="--", zorder=3)
        ax.set_xticks(range(len(PARALLEL)))
        ax.set_xticklabels([LABEL[b] for b in PARALLEL], fontsize=8)
        ax.set_title(NICE[topo].split("\n")[0])
        ax.set_ylim(0, 3.4)
    axes[0].set_ylabel("speedup over baseline")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.suptitle("The label above each pair is what the threads add: almost "
                 "nothing for one binary,\nand most of the result for the other",
                 y=0.99, fontsize=9)
    save(fig, "fig5_thread_scaling")
else:
    print("  skipped fig5: no thread-scaling data")

print("\ndone.")
