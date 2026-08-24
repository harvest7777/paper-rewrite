#!/usr/bin/env python3
"""Generate layered directed graphs with heavy edge crossings.

Nodes are split into equal layers. Each node points at FANOUT randomly chosen
nodes in the next layer, which is what produces crossings for mincross to work
on. Fixed seed, so the output is byte-identical on every run.
"""

import random

FANOUT = 3
SEED = 20260824

# (total nodes, number of layers) -- 100 nodes per layer throughout, so the
# layer count scales with size. Layers are the axis mincross parallelizes over.
CONFIGS = [(5000, 50), (10000, 100), (25000, 250)]


def generate(total_nodes: int, layers: int, path: str) -> None:
    random.seed(SEED)
    per_layer = total_nodes // layers
    node = lambda l, i: f"n{l}_{i}"

    with open(path, "w") as f:
        f.write("digraph crossings {\n")
        for l in range(layers):
            names = " ".join(node(l, i) for i in range(per_layer))
            f.write(f"  {{ rank=same; {names} }}\n")
        for l in range(layers - 1):
            for i in range(per_layer):
                for tgt in random.sample(range(per_layer), min(FANOUT, per_layer)):
                    f.write(f"  {node(l, i)} -> {node(l + 1, tgt)}\n")
        f.write("}\n")


for total, layers in CONFIGS:
    out = f"crossing-heavy-{total}-nodes.gv"
    generate(total, layers, out)
    print(f"wrote {out}  ({total} nodes, {layers} layers)")
