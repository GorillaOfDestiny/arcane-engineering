import logging
import os

import matplotlib.pyplot as plt
import numpy as np

from .components import Battery, Switch, Wire, Caster, Junction, Circuit

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def wrap_around(end_point,wrap_to = [0,0],buffer = 3.,ax = None):
    if ax is None:
        ax = plt.gca()
    wire_line = np.array([[end_point[0],end_point[0] + buffer,end_point[0] + buffer,wrap_to[0] - buffer,wrap_to[0] - buffer,wrap_to[0]],
                          [end_point[1],end_point[1],end_point[1] - buffer,end_point[1] - buffer,end_point[1],end_point[1]]])
    ax.plot(wire_line[0],wire_line[1])


def plot(comp_list, buffer=3., start_point=[0, 0], depth=0, ax=None):
    n_components = len(comp_list)
    start_point_init = start_point.copy()
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(5, 5))
    for i in range(n_components):
        if isinstance(comp_list[i], Junction) and "-" not in comp_list[i].name:
            end_points = comp_list[i].plot([start_point])
            # plot branches
            junction_close_points = []
            for k, scl in enumerate(comp_list[i + 1]):
                sub_end_point = plot(scl, start_point=end_points[k], depth=depth + 1, ax=ax)
                junction_close_points.append(sub_end_point)
            # plot closing
            end_point = comp_list[i + 2].plot(junction_close_points)[0]
            start_point = np.array(end_point)

        elif isinstance(comp_list[i], list) or (isinstance(comp_list[i], Junction) and "-" in comp_list[i].name):
            continue
        else:
            end_point = comp_list[i].plot(start_point)
            start_point = np.array(end_point)  # + np.array([buffer,0])
            # ax.plot([end_point[0],start_point[0],],[end_point[1],start_point[1],],c = 'r')
    if depth == 0:

        wrap_around(end_point, wrap_to=start_point_init, buffer=buffer, ax=ax)
        plt.show()
    else:
        return (end_point)


def main():
    b_test = Battery(2, name="Battery 1")
    b_test2 = Battery(2, name="Battery 2")
    b_test3 = Battery(2, name="Battery 3")
    b_test3.energy = 300
    s_test = Switch(2, name="Switch")

    c_test = Caster(2, name="Caster 1")
    w_test = Wire(2, name="TestingElement") # never used?
    w_test.color = 'grey'
    c_test2 = Caster(2, name="Caster 2")
    c_test3 = Caster(2, name="Caster 3")

    n_t_steps = 600
    test_circuit = Circuit([b_test, s_test, b_test2, b_test3, [c_test, c_test2, c_test3]], s_test, n_t_steps)

    LOGGER.debug(test_circuit)
    # --------simulation
    test_circuit.step()
    plot(test_circuit.components)

    check_wires = False

    for cn in test_circuit:
        if check_wires:
            plt.plot(test_circuit.t, test_circuit.Es[cn.name], label=cn.name)
        elif check_wires is False and ("wire" not in cn.name and "junction" not in cn.name):
            plt.plot(test_circuit.t, test_circuit.Es[cn.name], label=cn.name)
    plt.plot(test_circuit.t, test_circuit.ET, color='k', ls="--", label="Total Energy")
    plt.legend()
    plt.ylabel("Energy")
    plt.xlabel("Time Step")
    plt.yscale('log')
    plt.show()


if __name__ == "__main__":
    main()