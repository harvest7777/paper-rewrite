#!/usr/bin/env python3
"""Regenerate every figure in this directory from results/*.json.

    python3 make_figures.py

Requires matplotlib (pip install matplotlib). Reads only; writes fig1..fig5
as .pdf (for LaTeX) and .png (for eyeballing) into this directory.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, "..", "..", "results"))

# baseline / claude / codex, fixed order, never cycled
C = {"baseline": "#2a78d6", "claude": "#eb6834", "codex": "#1baf7a"}
NULL = "#6d6d6d"
PHASES = ["1", "2", "3", "full"]
PHASE_LABEL = {"1": "rank", "2": "+mincross", "3": "+position", "full": "+splines"}
STAGES = [("rank", "1", None), ("mincross", "2", "1"),
          ("position", "3", "2"), ("splines", "full", "3")]

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


def load(prefix):
    """-> {phase: {name: {'mean': ms, 'times': [ms...]}}}"""
    out = {}
    for ph in PHASES:
        path = os.path.join(RESULTS, f"{prefix}phase{ph}.json")
        rows = json.load(open(path))["results"]
        out[ph] = {}
        for r in rows:
            cmd = r["command"]
            name = next((n for n in list(C) + ["null-a", "null-b", "null-c"]
                         if f"/{n}/" in cmd), cmd)
            out[ph][name] = {"mean": r["mean"] * 1000,
                             "times": [t * 1000 for t in r["times"]]}
    return out


G5 = load("crossing-heavy-5000-nodes.gv-")
G10 = load("crossing-heavy-10000-nodes.gv-")
NT = load("nulltest-5000-")


def stages(d):
    """Per-stage cost by differencing adjacent cumulative phases."""
    return {name: {k: d[a][k]["mean"] - (d[b][k]["mean"] if b else 0)
                   for k in d[a]}
            for name, a, b in STAGES}


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.pdf / {name}.png")


# ---------------------------------------------------------------- fig 1
# Null test: three byte-identical binaries. Establishes the noise floor.
fig, axes = plt.subplots(1, 4, figsize=(9, 2.9))
names = ["null-a", "null-b", "null-c"]
for ax, ph in zip(axes, PHASES):
    vals = [NT[ph][n]["mean"] for n in names]
    spread = (max(vals) - min(vals)) / min(vals) * 100
    for i, n in enumerate(names):
        pts = NT[ph][n]["times"]
        ax.scatter([i] * len(pts), pts, s=9, color=NULL, alpha=0.55,
                   linewidths=0, zorder=2)
        ax.hlines(NT[ph][n]["mean"], i - 0.28, i + 0.28,
                  color="#111111", lw=1.6, zorder=3)
    ax.set_xticks(range(3))
    ax.set_xticklabels(["a", "b", "c"])
    ax.set_title(f"phase {ph}\nspread {spread:.1f}%")
    ax.set_xlim(-0.6, 2.6)
axes[0].set_ylabel("ms")
fig.tight_layout(rect=(0, 0, 1, 0.86))
fig.suptitle("Three byte-identical binaries, 5,000-node graph "
             "(10 runs each; black bar = mean)", y=0.99)
save(fig, "fig1_null_test")


# ---------------------------------------------------------------- fig 2
# Where baseline time goes, and how it shifts with graph size.
fig, ax = plt.subplots(figsize=(7.2, 2.2))
ramp = ["#b7d3f6", "#86b6ef", "#3987e5", "#1c5cab"]
for row, (label, d) in enumerate([("10,000 nodes", G10), ("5,000 nodes", G5)]):
    st = stages(d)
    total = d["full"]["baseline"]["mean"]
    left = 0.0
    for (name, _, _), color in zip(STAGES, ramp):
        w = st[name]["baseline"] / total * 100
        ax.barh(row, w, left=left, color=color, height=0.55,
                edgecolor="white", linewidth=1.5)
        if w > 6:
            ax.text(left + w / 2, row, f"{name}\n{w:.0f}%", ha="center",
                    va="center", fontsize=8,
                    color="white" if color == "#1c5cab" else "#14181f")
        left += w
ax.set_yticks([0, 1])
ax.set_yticklabels(["10,000 nodes", "5,000 nodes"])
ax.set_xlabel("share of baseline runtime (%)")
ax.set_xlim(0, 100)
ax.grid(False)
ax.set_title("Crossing minimization dominates at 5k; coordinate assignment "
             "overtakes it at 10k", loc="left")
save(fig, "fig2_phase_composition")


# ---------------------------------------------------------------- fig 3
# End-to-end result at both sizes, with every run plotted.
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
for ax, (label, d) in zip(axes, [("5,000 nodes", G5), ("10,000 nodes", G10)]):
    base = d["full"]["baseline"]["mean"]
    for i, k in enumerate(C):
        ax.bar(i, d["full"][k]["mean"], color=C[k], width=0.6, zorder=1)
        ax.scatter([i] * 10, d["full"][k]["times"], s=8, color="#14181f",
                   alpha=0.55, linewidths=0, zorder=3)
        if k != "baseline":
            ax.text(i, d["full"][k]["mean"] * 0.5, f"{base / d['full'][k]['mean']:.2f}x",
                    ha="center", color="white", fontsize=10, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels(list(C))
    ax.set_title(label)
axes[0].set_ylabel("full pipeline (ms)")
fig.suptitle("End-to-end layout time (bars = mean of 10 runs; dots = individual runs)",
             y=1.04)
save(fig, "fig3_end_to_end")


# ---------------------------------------------------------------- fig 4
# Per-run distributions. Shows phase 1 fully overlapping.
fig, axes = plt.subplots(1, 4, figsize=(9, 2.9))
for ax, ph in zip(axes, PHASES):
    for i, k in enumerate(C):
        pts = G5[ph][k]["times"]
        ax.scatter([i] * len(pts), pts, s=10, color=C[k], alpha=0.7,
                   linewidths=0, zorder=2)
        ax.hlines(G5[ph][k]["mean"], i - 0.28, i + 0.28,
                  color="#14181f", lw=1.4, zorder=3)
    ax.set_xticks(range(3))
    ax.set_xticklabels(["base", "cla", "cod"], fontsize=8)
    ax.set_title(f"phase {ph}\n({PHASE_LABEL[ph]})")
    ax.set_xlim(-0.6, 2.6)
axes[0].set_ylabel("ms")
fig.tight_layout(rect=(0, 0, 1, 0.86))
fig.suptitle("Every run, 5,000-node graph — phase 1 overlaps completely; "
             "phases 2-3 separate cleanly", y=0.99)
save(fig, "fig4_per_run_distributions")


# ---------------------------------------------------------------- fig 5
# Does the advantage hold as the graph grows?
fig, ax = plt.subplots(figsize=(4.6, 2.8))
sizes, x = ["5,000", "10,000"], [0, 1]
floor = 8.39  # worst-case identical-binary spread, fig 1
ax.axhspan(1.0, 1 + floor / 100, color="#c9c9c9", alpha=0.55, zorder=0)
ax.text(1.30, 1 + floor / 200, "noise floor", fontsize=7.5,
        color="#4c5663", va="center", ha="right")
for k in ["claude", "codex"]:
    ys = [G5["full"]["baseline"]["mean"] / G5["full"][k]["mean"],
          G10["full"]["baseline"]["mean"] / G10["full"][k]["mean"]]
    ax.plot(x, ys, "-o", color=C[k], label=k, lw=1.8, ms=5, zorder=3)
    for xi, y in zip(x, ys):
        ax.annotate(f"{y:.2f}x", (xi, y), textcoords="offset points",
                    xytext=(0, 7), ha="center", fontsize=8, color=C[k])
ax.axhline(1.0, color="#14181f", lw=1, ls="--", zorder=1)
ax.set_xticks(x)
ax.set_xticklabels(sizes)
ax.set_xlabel("graph size (nodes)")
ax.set_ylabel("end-to-end speedup")
ax.set_xlim(-0.25, 1.6)
ax.set_ylim(0.95, 1.75)
ax.legend(frameon=False, loc="upper left")
ax.set_title("Only one agent's advantage grows with the workload", loc="left")
save(fig, "fig5_scaling")

print("\ndone.")
