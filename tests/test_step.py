from arcane_engineering.components import Wire, Battery


def test_single_wire():
    wire = Wire(energy=0)
    wire.step()

    assert wire.energy == 0 # energy is not created


def test_single_battery():
    battery = Battery(energy=1)
    battery.step()

    assert battery.energy == 1 # energy is preserved


def test_happy_path(simple_circuit):
    assert simple_circuit["battery"].energy > 0 # ensure starting energy
    simple_circuit.step()
    for comp in simple_circuit:
        assert comp.energy == 0 # energy is spent
