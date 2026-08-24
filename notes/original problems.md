%====================Where to find things========================
% 1. git repo for this paper
% https://github.com/chunhualiao/Rapids2-CompilerGPT-dot-optimization
% branch pushed by Edwyn for this paper: https://github.com/chunhualiao/Rapids2-CompilerGPT-dot-optimization/tree/Rapids2-CompilerGPT-dot-optimization-side-branch  
% 2. paper review
% https://openreview.net/forum?id=88zyE3fJzQ#discussion

% ================== Fundation and background knowledge
% F1: Graphviz dot layout algorithm: what it does, how it is implemented, how to compile and run it
  % check out the gitab repo,  build, and run the dot program, measure some timing info. 

  % learn how to build and run the graphviz dot layout algorithm program and measure some performance.   
 % https://gitlab.com/graphviz/graphviz

 % Using VS code + cline + openrouter to help build and run, get initial performance of the algorithm
 % https://openrouter.ai/rankings
 % models : google/gemini-3-flash-preview , moonshotai/kimi-k2.5, x-ai/grok-4.1-fast

% F2. OpenMP basics : take a few online tutorials,
  % try to compile and run a few example OpenMP codes
  
% ### Key Issues Identified:

% ==================  OpenMP specific issues related to dot algorithm 

% Possibly repeat Edwyn's experiment described in the paper
% branch pushed by Edwyn for this paper: https://github.com/chunhualiao/Rapids2-CompilerGPT-dot-optimization/tree/Rapids2-CompilerGPT-dot-optimization-side-branch

  %%  related to Section 4.2 and 4.3 in the paper
  
% 4 - Algorithmic correctness of Listing 1 (transpose_step_parallel) is doubtful: marked swaps are applied sequentially without preventing adjacent/conflicting swaps; per-iteration accumulators (c0, c1) are undeclared in-scope and may be shared; use of non-standard functions (in_cross_count/out_cross_count) with no definitions.

% 5 - Scheduling inconsistency: text claims dynamic scheduling for irregular workloads while code listing uses schedule(static).

% 11 - Claims of false sharing reduction and detailed cache metrics lack clear, feasible measurement methodology on the stated platform.

% 8- Strong determinism claim (bit-exact PNG hashes across parallel runs) is not convincingly justified given potential nondeterminism in rendering and floating-point behavior.

% ================== experiment issues
% 7- Test suite description inconsistent with results: primary evaluation described with fixed 100 nodes and varying edges, yet results emphasize 1,000–2,000-node graphs (Figure 3, Appendix G).
    % related to Sec 4.3
    
% 9 - Statistical reporting gaps: CIs are claimed but not presented; 

% 9.2  "power > 0.8" assertion lacks effect sizes or power analysis details; 

% 9. 3 ± values in Table 2 are not defined as SD/SE/CI.

% 12- Reproducibility and versioning inconsistencies (e.g., Graphviz "dev.20250825" date and missing code/data links).

% ================== hardware platform specific issues
% 1- Apple M1 architecture mischaracterized: incorrect L2 size and references to L3 cache metrics; M1 does not have a conventional CPU L3 cache.
  %  ?? can we get a M1 apple computer? easier to reproduce the work

% 2- Contradictory environment/tooling: mentions using Linux perf but experiments are on macOS; Valgrind/Helgrind use on macOS Apple Silicon is likely infeasible.

% 3 - NUMA-aware optimization claims on a UMA (unified memory) system (Apple M1) are contradictory.


% ================== writting issues
% 6- Multiple broken or incorrect cross-references: references to non-existent Section 6 and Section 5.5; "Table ??" placeholder (page 15); mislabeling Table 3 on page 12.

% 10 - Literature and related-work inaccuracies/mis-citations (e.g., [11] described as foundational for parallel graph processing; [4]/[5] mismatched to described topics).

