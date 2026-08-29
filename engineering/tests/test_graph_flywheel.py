from engineering.app.graph_flywheel import GRAPH_EDGES, GRAPH_NODES, graph_definition


def test_flywheel_graph_is_closed_loop():
    definition = graph_definition()
    assert definition["mode"] == "closed_loop"
    assert definition["nodes"] == list(GRAPH_NODES)
    assert definition["edges"] == [list(edge) for edge in GRAPH_EDGES]
    assert definition["cycle"] == [GRAPH_NODES[-1], GRAPH_NODES[0]]
    assert len(GRAPH_NODES) == 10
    assert len(GRAPH_EDGES) == 9
    assert definition["interval_seconds"] >= 60


def test_graph_has_no_duplicate_nodes():
    assert len(set(GRAPH_NODES)) == len(GRAPH_NODES)
