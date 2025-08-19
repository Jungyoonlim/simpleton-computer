from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Node:
    value: int
    left: "Node | None" = None
    right: "Node | None" = None

def depth(node: Node | None) -> int: 
        if node is None: 
            return 0 
        return 1 + max(depth(node.left), depth(node.right))