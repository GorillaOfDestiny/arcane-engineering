import inspect
import matplotlib.pyplot as plt
import numpy as np
from exceptions import *

class component():
    def __init__(self,requires_input = True, level = 1,energy = 0,name = 'placeholder_name'):
        self.requires_input = requires_input
        self.previous_comp = None #component before
        self.next_comp = None #component after
        self.energy = energy #amount of energy in the component
        self.level = level
        self.name = name
        self.allow_input = True
        self.allow_output = True
        self.max_energy = 1
        #all components need a drawing function
        #   and also connecting points I think
        #   for now, let's just get them in one line
    def print_info(self):
        attributes = inspect.getmembers(self, lambda a:not(inspect.isroutine(a)))
        passed_atts = [a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]
        print(passed_atts)
    def step(self):
        #a placeholder
        pass

class Battery(component):
    def __init__(self,level = 1,energy = 100,name = "battery"):
        super().__init__(level = level,energy = energy,name = name)
        if level == 0:
            self.requires_input = False
        self.max_energy = 100

    def plot(self,start_point = (0,0),x_size = 0.25,y_size = 1,ax = None):
        if ax is None:
            ax = plt.gca()
        line1_x = [start_point[0],
                   start_point[0]]
        line1_y = [start_point[1] - y_size/2,
                   start_point[1] +y_size/2]
        line2_x = [start_point[0]+x_size,
                   start_point[0]+x_size]
        line2_y = [start_point[1] - y_size/4,
                   start_point[1] + y_size/4]
        ax.plot(line1_x,line1_y,color = 'k',ls = "-")
        ax.plot(line2_x,line2_y,color = 'k',ls = "-")
        end_point = [start_point[0] + x_size,start_point[1]]
        return(end_point)
    def step(self):
        pass

class Wire(component):
    def __init__(self,level = None,energy = 0,name = "wire"):
        super().__init__(level = level,energy = energy,name = name)
        self.energy_in_rate = 1
        self.energy_out_rate = 1
        self.color = 'r'
    def step(self):
        
        if self.previous_comp.energy > 0 and self.previous_comp.allow_output and self.energy < 1:
            self.previous_comp.energy -=1
            self.energy += 1
        if self.energy > 0 and self.next_comp.allow_input  and self.next_comp.energy + 1 < self.next_comp.max_energy:
            self.next_comp.energy += 1
            self.energy -= 1

    def plot(self,start_point = [0,0],x_size = 3,y_size = 0,ax = None):
        if ax is None:
            ax = plt.gca()
        line1 = np.array([[start_point[0],start_point[0] + x_size],
                          [start_point[1],start_point[1] + y_size]])
        ax.plot(line1[0,:],line1[1,:],color = self.color,ls = "-")
        return(line1[:,1])
        
class Caster(component):
    def __init__(self,level = 1,energy = 0,name = "caster"):
        super().__init__(level = level,requires_input=True,energy = energy,name = name)
        self.cast_threshold = 100
        self.allow_output=False
        self.max_energy = self.cast_threshold+1
    def cast(self):
        if self.energy>= self.cast_threshold:
            self.energy = 0
            return(True)
        else:
            return(False)
    
    def plot(self,start_point = (0,0),x_size = 1,y_size = 2,ax = None):
        if ax is None:
            ax = plt.gca()
        
        line1_x = [start_point[0],start_point[0] + x_size/2,start_point[0] + x_size]
        
        line1_y = [start_point[1],start_point[1] + y_size/2,start_point[1]]
        line2_y = [start_point[1],start_point[1] - y_size/2,start_point[1]]
        ax.plot(line1_x,line1_y,color = 'k',ls = "-")
        ax.plot(line1_x,line2_y,color = 'k',ls = "-")
        end_point = [start_point[0] + x_size,start_point[1]]

        return(end_point)
    
    def step(self):
        if self.energy >= self.cast_threshold:
            self.cast()
        else:
            pass

class Switch(component):
    def __init__(self,level = None,energy = 0,name = "switch",start_on = False):
        super().__init__(level = level,requires_input=True,energy = energy,name = name)
        self.allow_input = start_on
        self.allow_output = start_on
        self.color = 'k'
    def step(self):
        if self.allow_input and self.previous_comp.energy > 0 and self.previous_comp.allow_output:

            self.previous_comp.energy -=1
            self.energy += 1
        if self.energy > 0 and self.allow_output and self.next_comp.allow_input:

            self.next_comp.energy += 1
            self.energy -= 1
    def plot(self,start_point = (0,0),x_size = 2,y_size = 0.25,ax = None):
        if ax is None:
            ax = plt.gca()
        line1 = np.array([[start_point[0],start_point[0] + x_size*(1/3),start_point[0] + x_size*(2/3)],
                          [start_point[1],start_point[1],start_point[1] + y_size]])
        line2 = np.array([[start_point[0] + (2/3)*x_size,start_point[0] + x_size],[start_point[1],start_point[1]]])
        ax.plot(line1[0,:],line1[1,:],color = self.color,ls = "-")
        ax.plot(line2[0,:],line2[1,:],color = self.color,ls = "-")
        end_point = [start_point[0] + x_size,start_point[1] + 0]
        return(end_point)
    def toggle(self):
        self.allow_input = True
        self.allow_output = True

def connect(comp_list: list):
    n_components = len(comp_list)
    new_comp_list = []
    wire_i = 0
    for i in range(n_components):
        #print(i)
        j = (i+1)%n_components
        
        if comp_list[j].requires_input:
            wire_obj = Wire(None,0,name = f'wire {wire_i}')
            wire_i += 1
            comp_list[i].next_comp = wire_obj
            comp_list[j].previous_comp = wire_obj
            wire_obj.previous_comp = comp_list[i]
            wire_obj.next_comp = comp_list[j]
            wire_obj.level = wire_obj.previous_comp.level
            if wire_obj.level != wire_obj.next_comp.level:
                raise CircuitException(f"Wire object connecting {wire_obj.previous_comp.name} ({wire_obj.previous_comp.__class__.__name__}) and {wire_obj.next_comp.name} ({wire_obj.next_comp.__class__.__name__}) have different levels: {wire_obj.previous_comp.level} and {wire_obj.next_comp.level}")
            #comp_list[i].next_comp = comp_list[j]
            #comp_list[j].previous_comp = comp_list[i]
        else:
            comp_list[i].next_comp = None
    
        new_comp_list.append(comp_list[i])
        new_comp_list.append(wire_obj)
        #new_comp_list.append(comp_list[j])
    return(new_comp_list)

def wrap_around(end_point,wrap_to = [0,0],buffer = 3.,ax = None):
    if ax is None:
        ax = plt.gca()
    wire_line = np.array([[end_point[0],end_point[0] + buffer,end_point[0] + buffer,wrap_to[0] - buffer,wrap_to[0] - buffer,wrap_to[0]],
                          [end_point[1],end_point[1],end_point[1] - buffer,end_point[1] - buffer,end_point[1],end_point[1]]])
    ax.plot(wire_line[0],wire_line[1])


def plot(comp_list,buffer = 3.):
    n_components = len(comp_list)
    start_point = [0,0]
    start_point_init = start_point.copy()
    fig,ax = plt.subplots(1,1,figsize = (5,5))
    for i in range(n_components):
        end_point = comp_list[i].plot(start_point)
        start_point = np.array(end_point)# + np.array([buffer,0])
        #ax.plot([end_point[0],start_point[0],],[end_point[1],start_point[1],],c = 'r')

    wrap_around(end_point,wrap_to = start_point_init,buffer = buffer,ax = ax)
    plt.show()


if __name__ == "__main__":




    b_test = Battery(2,name = "Battery 1")
    b_test2 = Battery(2,name = "Battery 2")
    s_test = Switch(2,name = "Switch")
    c_test = Caster(2,name = "Caster 1")
    test_comp_list = [b_test,b_test2,s_test,c_test]
    new_comp_list = connect(test_comp_list)


    #--------simulation
    plot(new_comp_list)
    s_test.print_info()
    t = []
    n_t_steps = 400
    Es = np.zeros((len(new_comp_list),n_t_steps))
    for t_step in range(n_t_steps):
        
        if t_step == 100:
            s_test.toggle()
        t.append(t_step)
        for comp in new_comp_list:
            comp.step()
        for i in range(len(new_comp_list)):
            Es[i,t_step] = new_comp_list[i].energy
    check_wires = False
    
    for i,nc in enumerate(new_comp_list):
        if check_wires:
            plt.plot(t,Es[i],label = nc.name)
        elif check_wires is False and "wire" not in nc.name:
            plt.plot(t,Es[i],label = nc.name)
        
    plt.legend()
    plt.ylabel("Energy")
    plt.xlabel("Time Step")
    plt.show()
