import inspect
import logging

import matplotlib.pyplot as plt
import numpy as np

from . import exceptions

LOGGER = logging.getLogger(__name__)


class Component:
    def __init__(
        self,
        requires_input=True,
        level=1,
        energy=0,
        name="placeholder_name",
        *args,
        **kwargs,
    ):
        self.requires_input = requires_input
        self.previous_comp = None  # component before
        self.next_comp = None  # component after
        self.energy = energy  # amount of energy in the component
        self.level = level
        self.name = name
        self.allow_input = True
        self.allow_output = True
        self.max_energy = 2
        # all components need a drawing function
        #   and also connecting points I think
        #   for now, let's just get them in one line

    def print_info(self):
        attributes = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        passed_atts = [
            a for a in attributes if not (a[0].startswith("__") and a[0].endswith("__"))
        ]
        LOGGER.debug(f"--------info about {self.name}----------")
        for pa in passed_atts:
            LOGGER.debug(f"{pa[0]}: {pa[1]}")
        LOGGER.debug("===================")

    def step(self):
        # a placeholder
        pass

    def plot(self, start_point=(0, 0), x_size=1, y_size=1, ax=None):
        pass


class Battery(Component):
    def __init__(self, level=1, energy=100, name="battery"):
        super().__init__(level=level, energy=energy, name=name)
        if level == 0:
            self.requires_input = False
        self.max_energy = 1000

    def plot(self, start_point=(0, 0), x_size=0.25, y_size=1, ax=None):
        if ax is None:
            ax = plt.gca()
        line1_x = [start_point[0], start_point[0]]
        line1_y = [start_point[1] - y_size / 2, start_point[1] + y_size / 2]
        line2_x = [start_point[0] + x_size, start_point[0] + x_size]
        line2_y = [start_point[1] - y_size / 4, start_point[1] + y_size / 4]
        ax.plot(line1_x, line1_y, color="k", ls="-")
        ax.plot(line2_x, line2_y, color="k", ls="-")
        end_point = [start_point[0] + x_size, start_point[1]]
        return end_point


class Wire(Component):
    def __init__(self, level=None, energy=0, name="wire"):
        super().__init__(level=level, energy=energy, name=name)
        self.energy_in_rate = 1
        self.energy_out_rate = 1
        self.color = "r"

    def step(self):
        if self.previous_comp is None:
            self.previous_comp = self
        prev_energy = self.previous_comp.energy > 0
        prev_allow = self.previous_comp.allow_output
        self_thresh = self.energy < self.max_energy
        prev_junction = not isinstance(self.previous_comp, Junction)

        if prev_energy and prev_allow and self_thresh and prev_junction:
            de = min([self.previous_comp.energy, self.energy_in_rate])
            self.energy += de
            self.previous_comp.energy -= de

        de = self.energy  # min([self.energy_out_rate,self.energy])

        self_energy = self.energy > 0
        if self.next_comp is None:
            return self
        next_allow = self.next_comp.allow_input
        next_thresh = self.next_comp.energy + de < self.next_comp.max_energy
        next_not_junction = not isinstance(self.next_comp, Junction)

        if self_energy and next_allow and next_thresh and next_not_junction:
            self.next_comp.energy += de
            self.energy -= de

    def plot(self, start_point=[0, 0], x_size=3, y_size=0, ax=None):
        if ax is None:
            ax = plt.gca()
        line1 = np.array(
            [
                [start_point[0], start_point[0] + x_size],
                [start_point[1], start_point[1] + y_size],
            ]
        )
        ax.plot(line1[0, :], line1[1, :], color=self.color, ls="-")
        return line1[:, 1]


class Junction(Component):
    def __init__(self, n_inputs, n_outputs, level=None, energy=0, name="junction"):
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        super().__init__(level=level, energy=energy, name=name)
        self.energy_in_rate = 1
        self.energy_out_rate = 1

        if self.n_inputs != 1 or self.n_outputs != 1:
            # check this for simplicity. In theory we can have a 3 input 2 output case work but for this code
            # I think demanding at least one be 1 works better
            exceptions.CircuitException(
                f"In {self.name} either n_inputs or n_outputs must be 1. Instead found n_inputs = {self.n_inputs},n_outputs = {self.n_outputs}"
            )
        self.color = "purple"

    def step(self):
        # get energy from all possible inputs
        allowed_inputs = []

        for input_comp in range(self.n_inputs):
            # if self.name == "junction -0_0":
            #    print("i: ",self.previous_comp[input_comp].name,self.previous_comp[input_comp].energy,self.previous_comp[input_comp].allow_output)
            if (
                self.previous_comp[input_comp].energy > 0
                and self.previous_comp[input_comp].allow_output
            ):
                allowed_inputs.append(input_comp)
                # print(self.previous_comp[input_comp].energy)
        n_allowed_in = len(allowed_inputs)
        if n_allowed_in > 1:
            for i in allowed_inputs:
                if (
                    self.previous_comp[i].energy > 0
                    and self.previous_comp[i].allow_output
                    and self.energy < self.max_energy
                ):
                    self.energy += min(self.previous_comp[i].energy, 1) / n_allowed_in
                    self.previous_comp[i].energy -= (
                        min(self.previous_comp[i].energy, 1) / n_allowed_in
                    )
        elif n_allowed_in == 1:
            i = allowed_inputs[0]
            if (
                self.previous_comp[i].energy > 0
                and self.previous_comp[i].allow_output
                and self.energy < self.max_energy
            ):
                self.energy += min([self.previous_comp[i].energy, 1])
                self.previous_comp[i].energy -= min([self.previous_comp[i].energy, 1])
        # if self.name == "junction -0_0":
        #     print("after in: ",self.energy, n_allowed_in, self.previous_comp[input_comp].energy)
        #     print(self.previous_comp[1].name)
        # only if we have energy to output

        e_before = self.energy

        if e_before > 0:
            allowed_outputs = []

            for output_comp in range(self.n_outputs):
                if self.next_comp[output_comp].allow_input:
                    allowed_outputs.append(output_comp)
            n_allowed_out = len(allowed_outputs)
            remaining_idx = []
            for i in allowed_outputs:
                if (
                    self.next_comp[i].energy + e_before / n_allowed_out
                    < self.next_comp[i].max_energy
                ):
                    self.next_comp[i].energy += e_before / n_allowed_out
                    self.energy -= e_before / n_allowed_out
                    remaining_idx.append(i)

            # if any don't meet that requirement we need to spread the remainder out
            remaining_energy = self.energy

            for i in remaining_idx:
                self.next_comp[i].energy += remaining_energy / len(remaining_idx)
                self.energy -= remaining_energy / len(remaining_idx)

    def plot(self, start_point=[[0, 0]], x_size=2, y_size=2, ax=None, buffer=0.1):
        if ax is None:
            ax = plt.gca()
        assert len(start_point) == self.n_inputs, (
            f"Number of start_points differs from number of inputs to {self.name}"
        )

        # make all start_points at same x

        max_x = start_point[0][0]
        for sp in start_point:
            if sp[0] > max_x:
                max_x = sp[0]
        mid_y = np.mean([sp[1] for sp in start_point])

        junction_line = np.array(
            [
                [max_x + buffer + x_size / 2, max_x + buffer + x_size / 2],
                [mid_y + y_size / 2, mid_y - y_size / 2],
            ]
        )

        ax.plot(junction_line[0, :], junction_line[1, :], color=self.color)
        if self.n_inputs == 1:
            input_lines = np.array(
                [
                    [start_point[0][0], start_point[0][0] + x_size / 2],
                    [start_point[0][1], start_point[0][1]],
                ]
            )
            ax.plot(input_lines[0, :], input_lines[1, :], color=self.color)
        else:
            for i in range(self.n_inputs):
                input_x = [start_point[i][0], junction_line[0][0]]
                input_y = [start_point[i][1], start_point[i][1]]
                ax.plot(input_x, input_y, color=self.color)
        if self.n_outputs == 1:
            output_lines = np.array(
                [[junction_line[0][0], max_x + buffer + x_size], [mid_y, mid_y]]
            )
            end_points = [[max_x + buffer + x_size, mid_y]]
            ax.plot(output_lines[0, :], output_lines[1, :], color=self.color)
        else:
            end_points = []
            for i in range(self.n_outputs):
                output_y = np.linspace(
                    mid_y + y_size / 2, mid_y - y_size / 2, self.n_outputs
                )
                output_x = [junction_line[0][0], max_x + buffer + x_size]
                ax.plot(output_x, [output_y[i], output_y[i]], color=self.color)
                end_points.append([output_x[-1], output_y[i]])
        return end_points


class Caster(Component):
    def __init__(self, level=1, energy=0, name="caster"):
        super().__init__(level=level, requires_input=True, energy=energy, name=name)
        self.cast_threshold = 100
        self.allow_output = False
        self.max_energy = self.cast_threshold + 1

    def cast(self):
        if self.energy >= self.cast_threshold:
            self.energy = 0

    def plot(self, start_point=(0, 0), x_size=1, y_size=1.25, ax=None):
        if ax is None:
            ax = plt.gca()

        line1_x = [start_point[0], start_point[0] + x_size / 2, start_point[0] + x_size]

        line1_y = [start_point[1], start_point[1] + y_size / 2, start_point[1]]
        line2_y = [start_point[1], start_point[1] - y_size / 2, start_point[1]]
        ax.plot(line1_x, line1_y, color="k", ls="-")
        ax.plot(line1_x, line2_y, color="k", ls="-")
        end_point = [start_point[0] + x_size, start_point[1]]

        return end_point

    def step(self):
        if self.energy >= self.cast_threshold:
            self.cast()


class Blank(Component):
    def __init__(self, level=1, energy=0, name="blank"):
        super().__init__(level=level, requires_input=True, energy=energy, name=name)
        self.max_energy = 10000

    def plot(self, start_point=(0, 0), x_size=1, y_size=1.25, ax=None):
        return start_point


class Switch(Component):
    def __init__(self, level=None, energy=0, name="switch", start_on=False):
        super().__init__(level=level, requires_input=True, energy=energy, name=name)
        self.allow_input = start_on
        self.allow_output = start_on
        self.color = "k"

    def step(self):
        if (
            self.allow_input
            and self.previous_comp.energy > 0
            and self.previous_comp.allow_output
        ):
            self.previous_comp.energy -= 1
            self.energy += 1
        if self.energy > 0 and self.allow_output and self.next_comp.allow_input:
            self.next_comp.energy += 1
            self.energy -= 1

    def plot(self, start_point=(0, 0), x_size=2, y_size=0.25, ax=None):
        if ax is None:
            ax = plt.gca()
        line1 = np.array(
            [
                [
                    start_point[0],
                    start_point[0] + x_size * (1 / 3),
                    start_point[0] + x_size * (2 / 3),
                ],
                [start_point[1], start_point[1], start_point[1] + y_size],
            ]
        )
        line2 = np.array(
            [
                [start_point[0] + (2 / 3) * x_size, start_point[0] + x_size],
                [start_point[1], start_point[1]],
            ]
        )
        ax.plot(line1[0, :], line1[1, :], color=self.color, ls="-")
        ax.plot(line2[0, :], line2[1, :], color=self.color, ls="-")
        end_point = [start_point[0] + x_size, start_point[1] + 0]
        return end_point

    def toggle(self):
        self.allow_input = True
        self.allow_output = True


def connect(comp_list: list[Component], depth=0, branch_idx=None):
    wire_i = 0
    junc_i = 0
    if depth > 100:
        raise RecursionError("Depth exceed maximum (100) in connect")
    if not isinstance(comp_list, list):
        comp_list = [comp_list]  # if we have single component inputs

    n_components = len(comp_list)
    new_comp_list = []

    for i in range(n_components):
        if isinstance(comp_list[i], dict):
            LOGGER.debug(f"{''.join(['     '] * depth)}i: ", i, comp_list[i].name)
        else:
            LOGGER.debug(f"{''.join(['     '] * depth)}i: ", i, comp_list[i])
        j = (i + 1) % n_components
        if isinstance(comp_list[j], list):
            n_outputs = len(comp_list[j])
        else:
            n_outputs = 1

        if isinstance(comp_list[i], list):
            n_inputs = len(comp_list[i])
            continue  # should be handled already by junction code
        else:
            n_inputs = 1

        if n_outputs == 1 and n_inputs == 1:
            if comp_list[j].requires_input:
                wire_obj = Wire(
                    None,
                    0,
                    name=f"wire {wire_i}_{depth}_{branch_idx}"
                    if branch_idx is not None
                    else f"wire {wire_i}_{depth}",
                )
                wire_i += 1
                comp_list[i].next_comp = wire_obj
                comp_list[j].previous_comp = wire_obj
                wire_obj.previous_comp = comp_list[i]
                wire_obj.next_comp = comp_list[j]
                wire_obj.level = wire_obj.previous_comp.level
                if wire_obj.level != wire_obj.next_comp.level:
                    raise exceptions.CircuitException(
                        f"Wire object connecting {wire_obj.previous_comp.name} ({wire_obj.previous_comp.__class__.__name__}) and {wire_obj.next_comp.name} ({wire_obj.next_comp.__class__.__name__}) have different levels: {wire_obj.previous_comp.level} and {wire_obj.next_comp.level}"
                    )
                # comp_list[i].next_comp = comp_list[j]
                # comp_list[j].previous_comp = comp_list[i]
            else:
                comp_list[i].next_comp = None
            new_comp_list.append(comp_list[i])
            new_comp_list.append(wire_obj)
        else:
            # TODO
            #  [ ] Need to include the fact some branches technically don't need to return in the case of
            #       zeroth level components
            # opening junction
            junc_object_o = Junction(
                n_inputs, n_outputs, name=f"junction {junc_i}_{depth}"
            )

            # closing junction
            junc_object_c = Junction(
                n_outputs, n_inputs, name=f"junction -{junc_i}_{depth}"
            )

            # connect the list that the junctions connect
            sub_comp_lists = [
                connect(cl, depth=depth + 1, branch_idx=bi)
                for bi, cl in enumerate(comp_list[j])
            ]

            # check each individual branch
            for scl in sub_comp_lists:
                check_level(scl)
            # check all branches have the same
            check_level([scl[-1] for scl in sub_comp_lists])

            # connect junctions up
            junc_object_o.previous_comp = [comp_list[i]]
            junc_object_o.level = comp_list[i].level
            junc_object_o.next_comp = [scl[0] for scl in sub_comp_lists]
            junc_object_c.previous_comp = [scl[-1] for scl in sub_comp_lists]
            for scl in sub_comp_lists:
                scl[-1].next_comp = junc_object_c
            junc_object_c.next_comp = [
                comp_list[(j + 1) % n_components]
            ]  # as index j is the sublists
            junc_object_c.level = junc_object_c.previous_comp[0].level
            comp_list[i].next_component = junc_object_o
            new_comp_list.append(comp_list[i])
            new_comp_list.append(junc_object_o)
            new_comp_list.append(sub_comp_lists)
            new_comp_list.append(junc_object_c)

        # new_comp_list.append(comp_list[j])
        LOGGER.debug("i: ", i, new_comp_list)
    return new_comp_list


def flatten_circuit_components(comp_list):
    for comp in comp_list:
        if isinstance(comp, Circuit):
            yield from comp.components
        elif isinstance(comp, list):
            for subcomp in comp:
                if isinstance(subcomp, list):
                    for c in subcomp:
                        yield c
                else:
                    yield subcomp
        else:
            yield comp


class Circuit:
    def __init__(
        self,
        components: list[Component],
        switch: Switch,
        steps,
        depth: int = 0,
        branch_idx=None,
    ):
        self.components = connect(components, depth, branch_idx)
        self.switch = switch
        self.steps = steps
        self.t = []
        self.Es = {}
        self.names = []
        for cn in flatten_circuit_components(self.components):
            self.names.append(cn.name)
        for cn in self.names:
            self.Es[cn] = []
        self.ET = []

    def __getitem__(self, item):
        for comp in self.components:
            if isinstance(comp, Circuit) and item in comp:
                return comp[item]
            if hasattr(comp, "name") and comp.name == item:
                return comp

    def __iter__(self):
        return flatten_circuit_components(self.components)

    def __repr__(self):
        return self.names

    def get_component_names(self):
        return [c.name for c in flatten_circuit_components(self.components)]

    def step(self):
        comp_names = self.get_component_names()
        LOGGER.debug(comp_names)

        for t_step in range(self.steps):
            et = 0
            for c in flatten_circuit_components(self.components):
                self.Es[c.name].append(c.energy)
                et += c.energy
            self.ET.append(et)
            if t_step == 50:
                self.switch.toggle()
            self.t.append(t_step)
            for comp in self.components:
                if isinstance(comp, list):
                    for scl in comp:
                        for c in scl:
                            c.step()
                else:
                    comp.step()


def check_level(sub_comp_list):
    levels = [sc.level for sc in sub_comp_list]
    assert all([levels[0] == x for x in levels])


def get_n_components(comp_list):
    count = 0
    for comp in comp_list:
        if isinstance(comp, list):
            count += get_n_components(comp)
        else:
            count += 1
    return count
