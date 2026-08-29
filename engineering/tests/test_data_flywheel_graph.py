from engineering.app.data_flywheel_graph import EDGES, NODES, graph_description, run_graph


def test_graph_has_ten_bounded_nodes_and_release_cycle():
    assert len(NODES) == 10
    assert NODES[0].name == "Collector Agent"
    assert NODES[-1].name == "Release Gate Agent"
    assert EDGES["Release Gate Agent"] == ("Collector Agent",)


def test_graph_executes_one_complete_cycle_in_order():
    seen = []

    def execute(node):
        seen.append(node.name)
        return {"ok": True}

    transitions = run_graph(execute, max_cycles=1)
    assert seen == [node.name for node in NODES]
    assert len(transitions) == len(NODES)
    assert transitions[-1]["next"] == "Collector Agent"


def test_graph_is_bounded_and_describes_continuous_schedule_boundary():
    description = graph_description()
    assert description["continuous"] is True
    assert description["bounded_per_invocation"] is True
    assert description["cycle"] == "release_gate -> collector"
