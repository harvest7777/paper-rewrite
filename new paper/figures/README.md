# Figures

## Regenerate

```
cd "new paper/figures"
python3 make_figures.py
```

Needs `matplotlib` (`pip install matplotlib`). The script reads
`results/*.json` and writes nothing else — safe to re-run any time.
Each figure is written as `.pdf` (use this in LaTeX) and `.png` (to look at).

## What each one is

| File | Shows | Source data |
|---|---|---|
| `fig1_null_test` | Three byte-identical binaries at 5k. Establishes the noise floor: worst-case **8.4%** spread (phase 3), 4.2% end-to-end. | `nulltest-5000-phase*.json` |
| `fig2_phase_composition` | Where baseline time goes at 5k vs 10k. Mincross 49%→38%; position 23%→49%. | both graph sizes |
| `fig3_end_to_end` | Full-pipeline time, all three binaries, both sizes, every run plotted. | both graph sizes |
| `fig4_per_run_distributions` | All 10 runs per binary per phase at 5k. Phase 1 overlaps completely; phases 2–3 separate cleanly. | 5k |
| `fig5_scaling` | End-to-end speedup vs graph size, against the noise floor band. | both graph sizes |

## Notes

- Colors are fixed per binary — baseline blue, claude orange, codex green —
  and are the same in every figure. The set is CVD-safe.
- Stage costs in `fig2` are derived by differencing adjacent cumulative phases,
  which compounds the error of both terms. Treat as weaker evidence than the
  cumulative numbers.
- `fig5` has only two points. It is suggestive, not a fitted trend.
- The noise floor band in `fig5` uses 8.4%, the worst-case phase spread from
  `fig1`, not the 4.2% end-to-end figure — the conservative choice.
