def test_wires_added(simple_circuit):
    has_wire = False
    for comp in simple_circuit.components:
        if comp.name.startswith("wire"):
            has_wire = True
            break
    assert has_wire, "no wires found in circuit"
