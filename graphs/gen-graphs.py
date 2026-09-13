#!/usr/bin/env python3
"""Generate layered directed graphs.

Nodes are split into equal layers, and each node points at FANOUT randomly
chosen nodes in the next layer -- that is what produces the edge crossings
mincross has to resolve. Ranks are NOT pinned with rank=same, so dot computes
the layering itself; pinning it skips the ranking phase entirely.

Fixed seed, so output is byte-identical on every run.
"""

import random

SEED = 20260824

TOPOLOGIES = {
    "default": {"per_layer": 100, "fanout": 3},
    "sparse-deep": {"per_layer": 10, "fanout": 2},
    "dense-shallow": {"per_layer": 200, "fanout": 4},
}

SIZES = [5000]


def generate(total_nodes, per_layer, fanout, path):
    random.seed(SEED)
    layers = max(2, total_nodes // per_layer)
    width = min(per_layer, total_nodes)
    node = lambda l, i: f"n{l}_{i}"

    with open(path, "w") as f:
        f.write("digraph crossings {\n")
        for l in range(layers):
            f.write("  " + " ".join(node(l, i) for i in range(width)) + "\n")
        for l in range(layers - 1):
            for i in range(width):
                for tgt in random.sample(range(width), min(fanout, width)):
                    f.write(f"  {node(l, i)} -> {node(l + 1, tgt)}\n")
        f.write("}\n")

    return layers, width * layers, (layers - 1) * width * min(fanout, width)


for size in SIZES:
    for name, params in TOPOLOGIES.items():
        out = f"{size}-{name}.gv"
        layers, nodes, edges = generate(size, params["per_layer"], params["fanout"], out)
        print(f"wrote {out:26} {nodes:6} nodes  {edges:7} edges  {layers:4} layers")
