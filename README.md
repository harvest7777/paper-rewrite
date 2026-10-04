# Two Coding Agents Optimize GraphViz

Artifact for the paper in `new paper/`. Eight autonomous agent runs (Claude Code
and Codex, two prompts, two repetitions each) tried to make GraphViz's `dot`
faster. This repo holds the prompts, evaluation graphs, benchmark and
correctness harnesses, every raw measurement, and the paper source.

The agents' code is **not** in this repo. Each run lives in its own GitHub
repository on branch `agent-work`, and must be cloned into `sandboxes/` before
anything can be built.

## Setup

Every step runs from the repository root. The harness was written for macOS on
Apple Silicon; see [Platform notes](#platform-notes) for anything else.

### 1. Tools

```bash
brew install cmake bison hyperfine python@3.11
# For building the paper only:
brew install --cask mactex-no-gui   # provides latexmk and pdflatex
```

The paper's numbers were measured with `hyperfine` 1.20.0, CMake 4.3, Apple
Clang 17 and Python 3.11.

### 2. Python environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. Clone the eight agent runs and the baseline

Each run goes into `sandboxes/<name>/graphviz`. The folder names are fixed: the
scripts refer to them directly.

```bash
mkdir -p sandboxes
while read -r name repo; do
  git clone --branch agent-work "https://github.com/harvest7777/$repo.git" "sandboxes/$name/graphviz"
done <<'EOF'
claude            claude-graphviz-run
claude_2          claude-2-graphviz-run
claude_parallel   claude-parallel-graphviz-run
claude_parallel_2 claude-parallel-2-graphviz-run
codex             codex-graphviz-run
codex_2           codex-2-graphviz-run
codex_parallel    codex-parallel-graphviz-run
codex_parallel_2  codex-parallel-2-graphviz-run
EOF
```

The baseline is **`timestamped`**. It is unmodified GraphViz at commit
`23b06521` plus one commit, `0405c8582`, that adds per-phase timing behind the
`GV_PHASE_TIMING` environment variable. Every agent run carries the same timing
commit, so the baseline differs from them only in the agents' changes. It has
no repository of its own; take that commit from any run that branches from it:

```bash
git clone https://github.com/harvest7777/claude-parallel-graphviz-run.git sandboxes/timestamped/graphviz
git -C sandboxes/timestamped/graphviz checkout -b agent-work 0405c858241e9f67d66eeafc7986984107c73d6c
```

The name `timestamped` appears in the raw result files, so it is kept as is.
Read it as "baseline" everywhere.

### 4. Verify

Each sandbox's `HEAD` must match this table:

```bash
for d in sandboxes/*/graphviz; do echo "$d $(git -C "$d" rev-parse --short=9 HEAD)"; done
```

| Sandbox | HEAD |
|---|---|
| `claude` | `7744945b9` |
| `claude_2` | `f904830da` |
| `claude_parallel` | `79237d95a` |
| `claude_parallel_2` | `966486b5e` |
| `codex` | `1c9e0dcec` |
| `codex_2` | `5925de59e` |
| `codex_parallel` | `d81b58475` |
| `codex_parallel_2` | `43d9aa2bb` |
| `timestamped` | `0405c8582` |

### 5. Build

```bash
./01-build-binaries.sh
```

This builds all nine sandboxes with identical flags into `binaries/<name>/`,
with intermediate files in `builds/<name>/`. It skips any sandbox whose
`binaries/<name>` already exists, so delete that folder to rebuild one. The
installed binaries take about 50 MB and the build trees about 400 MB in total. Check that every sandbox printed `OK`, and that
`binaries/<name>/bin/dot` exists for all nine.

## Reproducing the paper

The evaluation graphs are already committed in `graphs/`.
`graphs/gen-graphs.py` regenerates them byte for byte from a fixed seed.

| Step | Command | Writes | Time |
|---|---|---|---|
| Benchmark | `SIZE=5000 ./02-run.sh` and `SIZE=10000 ./02-run.sh` | `results/*.json`, `results/phases/` | hours |
| Correctness (test suite) | `./03-test.sh` | stdout | long |
| Thread decomposition | `SIZE=5000 ./04-thread-scaling.sh` and `SIZE=10000 ./04-thread-scaling.sh` | `results/thread-scaling/` | hours |
| Figures | `cd "new paper/figures" && ../../.venv/bin/python make_figures.py` | `new paper/figures/*.pdf, *.png` | seconds |
| Paper | `cd "new paper" && latexmk -pdf main.tex` | `new paper/main.pdf` | seconds |

Benchmarks are timing-sensitive. Run them on an idle machine on mains power,
and run one at a time.

New benchmark runs write files tagged with the current date and time beside
the existing ones; they do not overwrite them. The figure script reads every
matching file in `results/`, so move the committed results aside first if you
want figures from a fresh run alone.

The correctness sweeps reported in the paper are archived with their output in
`results/correctness/`. Those three scripts `cd` to the original author's home
directory, so edit their `cd` line to point at this repository before running
them.

## Layout

| Path | Contents |
|---|---|
| `prompts/` | Both agent prompts, verbatim, and the prompt used to get each session's time and token usage. |
| `graphs/` | Graph generator and the six evaluation graphs (three shapes × 5,000 and 10,000 nodes). |
| `01`–`04-*.sh` | Build, benchmark, correctness and thread-decomposition harnesses, in run order. |
| `results/` | Raw data: `hyperfine` JSON, per-phase logs (`phases/`), thread scaling (`thread-scaling/`), correctness sweeps (`correctness/`), per-run session dumps (`dumps/`). |
| `new paper/` | Paper source. `figures/make_figures.py` regenerates every figure from `results/`. |
| `notes/` | Working notes from the original study. |
| `sandboxes/`, `binaries/`, `builds/` | Git-ignored. Created by setup steps 3 and 5. |

Each run's report is `OPTIMIZATION_REPORT.md` at the root of its sandbox. To see
a run's full diff, use `git -C sandboxes/<name>/graphviz diff 23b06521 agent-work`.

## Platform notes

- `01-build-binaries.sh` passes the Homebrew Bison path
  `/opt/homebrew/opt/bison/bin/bison`, because macOS's own Bison is older than
  GraphViz needs. On Linux, change `-DBISON_EXECUTABLE` to the system `bison`
  (3.0 or newer).
- `thread-identity-eval.sh` uses macOS `md5 -q`; on Linux use `md5sum`.
- The two parallel Claude runs choose their own thread counts. One uses every
  online core; the other uses the performance cores on Apple Silicon and every
  online core elsewhere. Thread counts, and so timings, will differ on other
  hardware. Set `GV_THREADS` to fix the count.
