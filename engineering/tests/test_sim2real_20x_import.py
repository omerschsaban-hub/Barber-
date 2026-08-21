def test_shared_sim2real_contract_imports():
    from app.sim2real_20x import CAPABILITIES, EvidenceKind, Sim2RealState

    assert len(CAPABILITIES) == 20
    assert EvidenceKind.PHYSICAL.value == "physical"
    assert Sim2RealState().stage == "cad"
