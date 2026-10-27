from ai_engine.graph.algorithms import MobilityGraph


def test_mobility_graph_shortest_path():
    graph = MobilityGraph()
    graph.add_edge("A", "B", 5, 0.1, 0.2)
    graph.add_edge("B", "C", 5, 0.1, 0.2)
    graph.add_edge("A", "C", 20, 0.1, 0.2)
    cost, path = graph.shortest_path("A", "C", "fastest")
    assert cost == 10
    assert path == ["A", "B", "C"]

