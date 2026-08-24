Correctness: Mac OS has trouble in running ctests with all the dependencies
* try one  more time to resolve the linking error with catch2
  cannot fix it. filed a ticket:
  https://gitlab.com/graphviz/graphviz/-/issues/2706

if still not working
* a workaround: still use Mac OS for performance optimization: easier experiments
* when testing correctness of optimizations, using a redhat or ubutn machine to run ctests


# GraphViz Performance Optimization & Publication Plan

GraphViz's dot program provides graph layout capabilities, but its layout algorithm does not scale well to large graphs. This document outlines a concrete plan for additional experiments and writeup to prepare a final draft suitable for submission to a top-tier conference.

(IEEE VIS, EuroVis, SIGGRAPH, ICSE, FSE, USENIX ATC)


Additional experiments (e.g., ablation, scalability, quality-vs-speed, comparison to state-of-the-art, visual analysis, reproducibility).

---

## 1. Reproduce and Record the Problem

First, we need to establish a baseline by reproducing the problem with concrete input dot files and measuring performance metrics:

### 1.1 Build Environment Setup
- Ensure Apple's LLVM 17 back-end is installed and configured
- Verify all dependencies are available (cmake, make, etc.)

### 1.2 Build and Install GraphViz
- Clone the repository if not already done: `git clone https://gitlab.com/graphviz/graphviz.git`
- Configure with default compilation options: `cmake -S . -B build`
- Build the project: `cmake --build build --target dot --config Release`
- Install: `cmake --build build --target install`

### 1.3 Benchmark Dataset Creation
- Collect 3-5 dot graphs with different sizes:
  - Small graph (~100 nodes)
  - Medium graph (~1,000 nodes)
  - Large graph (~10,000 nodes)
  - Very large graph (~50,000+ nodes, if available)
- Sources for test graphs:
  - GraphViz test suite in `graphs/` directory
  - Public graph repositories
  - Generated graphs using tools like `gvgen`

### 1.4 Baseline Performance Measurement
- Create a benchmark script to measure:
  - Total execution time
  - Memory usage
  - CPU utilization
  - Layout quality metrics
- Run each test graph 5 times and record average metrics
- Document baseline results in a structured format for later comparison

## 2. Optimization Strategy

Below is a "hit-list" of optimizations to try on an M3 Max MacBook Pro, ordered by effort required versus expected speed-up on very large dot graphs (≥ 10k nodes).

### 2.1 Get the Code & Build it Native

| Step                       | Why it matters on Apple Silicon                                                                                        | How                                                                                                                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Clone tip-of-tree**      | Avoids bugs already fixed since the last tarball                                                                       | `git clone https://gitlab.com/graphviz/graphviz.git` (GitHub mirror exists but GitLab is canonical) ([graphviz.org][1])                                                   |
| **Compile with LTO + PGO** | Apple's LLVM 17 back-end can remove 10-20 % of runtime just by cross-module inlining and profile-guided block ordering | `bash\nbrew install libomp\ncmake -S . -B build -DCMAKE_C_COMPILER=clang -DCMAKE_C_FLAGS="-O3 -flto -mcpu=apple-m3"\ncmake --build build --target dot --config Release\n` |
| **Use `-ftime-trace`**     | Produces per-function JSON timing that CompilerGPT can ingest automatically                                            | add `-ftime-trace` to `CMAKE_C_FLAGS` and run a large graph once to collect the profile                                                                                   |

Graphviz's core is still overwhelmingly **C (≈ 72 %)**, with a thin layer of C++, Python helpers and build scripts ([github.com][2]). That means the plain Clang tool-chain works; no Rust/Go tool-chain headaches.

### 2.2 Quick Runtime Flags (Zero Code Changes)

| Flag                                    | What it does                             | Typical effect on big graphs           |
| --------------------------------------- | ---------------------------------------- | -------------------------------------- |
| `-Gpack=true`                           | Packs connected components before layout | 1.2 × faster if your graph is a forest |
| `-Gsplines=line`                        | Avoids cubic-spline routing phase        | 1.1 – 1.4 × faster, big RAM drop       |
| `-Gmaxiter=200` (default = 24\*#layers) | Limits iterative crossing-min pass       | Smooths out worst-case O(n³) blow-ups  |

Testing methodology:
- Create a test matrix of flag combinations
- Run each combination on the benchmark dataset
- Analyze the Pareto front for "speed vs. drawing quality"
- Document optimal flag combinations for different graph sizes and types

### 2.3 Compiler-Level Optimizations

1. **PGO Two-Stage Build**

   ```bash
   # Stage 1: Build with profile generation
   cmake --build build --config Release --target install/strip \
         -- CFLAGS="-fprofile-instr-generate"
   
   # Generate profile data
   ./install/bin/dot monster.dot -Tsvg > /dev/null
   
   # Stage 2: Rebuild using profile data
   cmake --build build --config Release --target all \
         -- CFLAGS="-fprofile-instr-use=default.profdata"
   ```

   Expected improvement: **15-25%** off `networksimplex()` on ARM cores.

2. **Link-time Vectorization**
   - Add `-ftree-vectorize -fveclib=Accelerate` to CFLAGS
   - Enables Clang to emit NEON instructions for the tight barycentric-sort loops
   - Benchmark before and after to measure improvement

3. **Memory Allocator Optimization**
   - Test with jemalloc: `brew install jemalloc` and link against it
   - Alternative: Set `MallocNanoZone=0` environment variable
   - Addresses zone locking stalls on >12 cores due to millions of small allocations

### 2.4 Low-Touch Code Patches

| Patch idea                                                                                                                                | Effort                           | Expected gain                                   |
| ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ----------------------------------------------- |
| **Arena allocator for `gv_malloc()`** (lib/common/memory.c)                                                                               | \~50 LOC                         | 1.3 × on spline routing (fewer `malloc`/`free`) |
| **Parallel crossing-minimisation** – wrap the outer rank loop of `mincross.c:transpose()` in `#pragma omp parallel for schedule(dynamic)` | \~20 LOC once libomp is in place | 2-5× on 16P-core M3 Max                         |
| **Coarsening pre-pass for network-simplex** (Hu & Gansner 2010)                                                                           | few hundred LOC                  | super-linear speed-up on graphs > 30k nodes     |

Implementation approach:
1. Analyze hotspots using `ftime-trace` and performance profiling
2. Draft patches for each optimization
3. Test each patch individually to measure impact
4. Combine compatible optimizations for maximum effect

### 2.5 GPU / Metal Experiments (Stretch Goal)

Apple's Metal Performance Shaders don't yet have an off-the-shelf bipartite crossing-min kernel, but the barycentric ordering step maps cleanly to a prefix-sum + sort network:

```cpp
// pseudocode
computeRanks<<<grid,block>>>(…);
for (int iter=0; iter<k; ++iter) {
    metal::device_vector<float> bary = reduceByRank(…);
    gpuBitonicSort(bary);
}
```

Implementation steps:
1. Identify parallelizable components in the algorithm
2. Create Metal shader implementations
3. Integrate with GraphViz codebase
4. Benchmark and optimize

Note: Expect order-of-magnitude acceleration **only** for very dense layer pairs; start with CUDA research code and port to Metal.

### 2.6 Test & Regression Safety-Net

* The repo ships a traditional **`tests/`** and older **`rtest/`** harnesses; `make check` or `ctest` will render reference graphs and diff them ([github.com][2]).
* The Graphviz maintainers admit the image-diff tests are flaky, but they're good for catching outright crashes ([forum.graphviz.org][3]).
* Hook these tests into your CI so every CompilerGPT-generated patch runs them before you accept the speed-up.

Testing strategy:
1. Run the full test suite before any optimization to establish baseline
2. After each optimization, run tests to ensure correctness
3. Create additional tests for large graphs if needed
4. Document any visual differences in output and determine acceptability

## 3. Implementation Timeline

#### Suggested Order of Attack

1. **Baseline numbers + flag tuning** (hours)
   - Build with default options
   - Collect benchmark data
   - Test runtime flags

2. **LTO + PGO rebuild** (half a day)
   - Implement compiler optimizations
   - Measure improvement over baseline

3. **Allocator & OpenMP patches** (1–2 days)
   - Implement memory allocator optimizations
   - Add OpenMP parallelization
   - Test and measure improvements

4. **Multilevel ranking refactor** (1 week)
   - Implement coarsening pre-pass
   - Test with large graphs
   - Refine implementation

5. **GPU prototype** (as time allows)
   - Implement Metal shaders
   - Integrate with GraphViz
   - Benchmark and optimize

With this sequence, we should see a quick **2–3×** speed-up on an M3 Max, and a clear path toward an order-of-magnitude improvement as deeper changes land.

## 4. Additional Experiments for Publication

To strengthen the paper for a top-tier conference, we will conduct the following additional experiments:

### 4.1 Ablation Studies
- Systematically disable/enable each optimization (flags, LTO, PGO, allocator, OpenMP, etc.) and measure the impact on performance and layout quality.
- Present results in a table and as bar/line plots.

### 4.2 Scalability Experiments
- Test on graphs up to 100k+ nodes and edges.
- Measure time, memory, and success/failure rates.
- Compare with other state-of-the-art graph layout tools (e.g., yEd, OGDF, Graph-tool, NetworkX, Gephi, D3/Dagre.js, Graphistry).

### 4.3 Quality vs. Speed Tradeoff
- Quantitatively and visually compare layout quality (e.g., edge crossings, aspect ratio, readability) for different optimization levels and tools.
- Include side-by-side visualizations for representative graphs.

### 4.4 Robustness and Reproducibility
- Test on a diverse set of real-world and synthetic graphs (random, scale-free, grid, etc.).
- Provide scripts and data for full reproducibility.

### 4.5 Profiling and Bottleneck Analysis
- Use ftime-trace and other profilers to analyze remaining bottlenecks after each optimization.
- Report function-level breakdowns and discuss remaining challenges.

---

## 5. Writeup Plan for Top-Tier Conference Submission

### 5.1 Paper Structure
- Abstract
- Introduction (motivation, contributions)
- Related Work (updated with latest literature)
- Background (dot algorithm, complexity)
- Methodology (experimental setup, datasets, metrics)
- Optimization Strategies (with implementation details)
- Experiments and Results (all new experiments above)
- Discussion (tradeoffs, limitations, lessons learned)
- Conclusion and Future Work
- References
- Appendix (scripts, reproducibility, build instructions)

### 5.2 Deliverables
- Camera-ready LaTeX paper (max 10-12 pages, double-column)
- Artifact package (code, data, scripts, Dockerfile)
- Slide deck for oral presentation

---

## 6. Target Conference Venues and Deadlines

### Recommended Venues
- **IEEE VIS (Visualization & Visual Analytics)**
  - https://ieeevis.org/
  - Typical deadline: Early April (for October conference)
- **EuroVis (Eurographics/IEEE Visualization Symposium)**
  - https://www.eurovis.org/
  - Typical deadline: Early March (for June conference)
- **SIGGRAPH (ACM Conference on Computer Graphics and Interactive Techniques)**
  - https://s2025.siggraph.org/
  - Typical deadline: January (for August conference)
- **ICSE (International Conference on Software Engineering)**
  - https://conf.researchr.org/home/icse-2026
  - Typical deadline: September (for May conference)
- **FSE (ACM SIGSOFT Symposium on the Foundations of Software Engineering)**
  - https://conf.researchr.org/home/fse-2025
  - Typical deadline: May (for November conference)
- **USENIX ATC (Annual Technical Conference)**
  - https://www.usenix.org/conference/atc25
  - Typical deadline: January (for July conference)

> **Action:** Check the official conference websites for the most up-to-date submission deadlines and requirements.

---

## 7. Timeline and Checklist

- **Week 1:** Complete all additional experiments (ablation, scalability, quality, profiling)
- **Week 2:** Analyze results, generate plots, and update all figures/tables
- **Week 3:** Draft new sections for experiments, results, and discussion
- **Week 4:** Revise related work, finalize all sections, and prepare artifact package
- **Week 5:** Internal review, address feedback, and prepare for submission

---

## 8. Documentation and Reporting

For each optimization and experiment:
1. Document implementation details and rationale
2. Record performance and quality improvements with metrics and plots
3. Note any trade-offs or limitations
4. Ensure all scripts and data are reproducible and available

Final report should include:
- Summary of all optimizations and experiments
- Cumulative performance and quality improvement
- Recommendations for future work
- Lessons learned
- Submission-ready paper and artifact package

---

[1]: https://graphviz.org/download/source/ "Source Code | Graphviz"
[2]: https://github.com/applied-machinelearning/graphviz "GitHub - applied-machinelearning/graphviz"
[3]: https://forum.graphviz.org/t/getting-rtest-to-run-in-continuous-integration/134 "Getting rtest to run in continuous integration - Dev - Graphviz"
