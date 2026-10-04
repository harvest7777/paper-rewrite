# Figures

## Regenerate

```
cd "new paper/figures"
python3 make_figures.py
```

Needs `matplotlib`. The script reads `results/` and writes nothing else.
Each figure is written as `.pdf` (used by LaTeX) and `.png` (to look at).

| File | Shows | Source |
|---|---|---|
| `fig2_phase_composition` | Baseline phase shares across three topologies at fixed node count. | `results/phases/` |
| `fig3_end_to_end` | Layout time per binary per topology, every run plotted. | `*-full-perm*.json` |
| `fig4_phase_speedup` | Per-phase speedup for both agents on all three topologies. | `results/phases/` |
| `fig5_thread_scaling` | The two parallel Claude binaries at one thread and at their own default, as speedup over baseline. | `results/thread-scaling/` |

## Notes

- Colors are fixed per binary -- baseline blue, claude orange, codex green --
  and identical across figures. The set is CVD-safe.
- Phase costs are measured inside the process, not derived by differencing, so
  they carry no compounded error.
- The noise floor is a table in the paper, derived from the baseline's spread
  across command orderings. It is not a figure.
- Figures 2--4 use the 5,000-node data. The 10,000-node results are tables in
  the paper, not figures. Figure 5 covers both sizes.
