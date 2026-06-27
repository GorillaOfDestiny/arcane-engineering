import pytest

from arcane_engineering.components import Battery, Wire, Switch, Caster, connect, Circuit


@pytest.fixture
def simple_circuit():
    battery = Battery(level=2, energy=300)
    switch = Switch(level=2)
    caster = Caster(level=2)
    circuit = Circuit([battery, switch, caster], switch, 600)

    return circuit