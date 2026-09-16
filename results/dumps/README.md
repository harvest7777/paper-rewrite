# Session dumps

One file per agent run, named for the sandbox it came from. Each records the
model, the time the run took, and the token counts its session log reported.

| file | paper label | prompt | agent |
|---|---|---|---|
| `claude.md` | Claude 1 | base | Claude Code |
| `claude_2.md` | Claude 2 | base | Claude Code |
| `claude_parallel.md` | Claude 1 P | parallelism | Claude Code |
| `claude_parallel_2.md` | Claude 2 P | parallelism | Claude Code |
| `codex.md` | Codex 1 | base | Codex |
| `codex_2.md` | Codex 2 | base | Codex |
| `codex_parallel.md` | Codex 1 P | parallelism | Codex |
| `codex_parallel_2.md` | Codex 2 P | parallelism | Codex |

## Reading these

The two agents count tokens differently and the dumps preserve each one's own
categories rather than converting between them. Claude reports input, output,
cache creation and cache read, which sum to its total. Codex reports a total
with cached input as a subset of input and reasoning output as a subset of
output.

The time fields are not uniformly labelled either. `claude_2.md` reports working
time with idle excluded, and records that idle was zero. `claude_parallel.md`
and `claude_parallel_2.md` report a raw wall span. `claude.md` reports both, and
its working time excludes one pause. The paper reports a single time per run and
labels it working time; for every run except `claude.md` that is the wall span.

`claude.md` and `codex.md` were originally a single combined `dump.txt` at the
repository root, recovered from git history and split here.
