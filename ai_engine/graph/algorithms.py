from __future__ import annotations

import heapq
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Edge:
    target: str
    time_cost: float
    safety_cost: float
    fuel_cost: float


class MobilityGraph:
    def __init__(self) -> None:
        self.edges: dict[str, list[Edge]] = defaultdict(list)

    def add_edge(self, source: str, target: str, time_cost: float, safety_cost: float, fuel_cost: float) -> None:
        self.edges[source].append(Edge(target, time_cost, safety_cost, fuel_cost))

    def shortest_path(self, source: str, target: str, mode: str = "balanced") -> tuple[float, list[str]]:
        weights = {
            "fastest": (1.0, 0.0, 0.0),
            "safest": (0.45, 0.45, 0.10),
            "fuel": (0.35, 0.10, 0.55),
            "balanced": (0.55, 0.25, 0.20),
        }.get(mode, (0.55, 0.25, 0.20))
        queue = [(0.0, source, [source])]
        visited = set()
        while queue:
            cost, node, path = heapq.heappop(queue)
            if node == target:
                return cost, path
            if node in visited:
                continue
            visited.add(node)
            for edge in self.edges[node]:
                if edge.target not in visited:
                    edge_cost = edge.time_cost * weights[0] + edge.safety_cost * weights[1] + edge.fuel_cost * weights[2]
                    heapq.heappush(queue, (cost + edge_cost, edge.target, path + [edge.target]))
        return float("inf"), []

