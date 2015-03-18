# -*- coding: utf-8 -*-
"""
Damped harmonic oscillator agent model

Motion for the damped oscillator is described as:

m*(d^2x/dt^2) + 2*zeta*w0*(dx/dt) + w0^2*x + [driving forces] = 0

where x is the positon of the oscillator in one dimension, w0 i the frequency,
zeta is the damping coefficient, and m is mass.

w0 is the natural frequency of the harmonic oscillator, which is:
w0 = sqrt(k/m)

Driving forces are to be implemented. The first will be a force
in a uniform random direction: F(t). The second will be bias, which will be 
a functionof the temperature at the current position at the current time: 
b(T(x,t)).

A second order ODE (odeint) is used to solve for the position of the mass,
presently in 1D.

End goal: run in 2d, add driving forces (random or otherwise) and add spatial
and/or temperature-stimulus Bias.

Created on Mon Mar 16 16:22:47 2015
@authors: Richard Decal, decal@uw.edu
        Sharri Zamore

https://staff.washington.edu/decal/
https://github.com/isomerase/

Code forked from Lecture-3-Scipy.ipynb from the SciPy lectures:
https://github.com/jrjohansson/scientific-python-lectures
authored by J.R. Johansson (robert@riken.jp) http://dml.riken.jp/~rob/

Variable names have been changed to reflect terms in the original equations.
"""
from scipy.integrate import odeint, ode # TODO: delete ode? unused... -rd
from matplotlib import pyplot as plt
import numpy as np

# CONSTANTS. TODO: make user-input.-sz
# TODO: all caps for constant naming conventions -rd
m = 5   # mass of agent
k = 0.001   # spring constant
w0 = np.sqrt(k/m)
zeta = 20   # maybe rename? I don't like using the same name for the ode input and the function -sz


# TODO: make Bias a class? Talk to Rich P about a smart way to make this object oriented. -sz

# Initial state of the spring.
# TODO: should we construct y0 for the 2D? or, should we just put everything
# the x0 vector, and change x0[0] from a float to a tuple, and x0[1] from a 
# float to a vector? -rd
x0 = [1.0, 0.0]  # position_0, velocity_0
#y0 = [1.0 0.0]  # TODO: rename y, we will need that when we expand to 2D -sz
# unclear of how this is determined. -sz

# Time coodinates to solve the ODE for
dt = 1  # timebin width
runtime = 1000
num_dt = runtime/dt  # number of timebins
t = np.linspace(0, runtime, num_dt)


def baselineDrivingForce():
    """Will eventually be a 2D unit-vector. For now, using just the x-component
    since we are only working in 1 dimension.
    """
    rand_radians = np.random.uniform(0, 2*np.pi)  # high bound is not inclusive
    x_component = 0.000001 * np.cos(rand_radians)
    y_component = 0.000001 * np.sin(rand_radians)
    return x_component


def tempNow():
    """Given position and time, lookup nearest temperature (or interpolate?)"""
    pass


def biasedDrivingForce():
    """biased driving force, determined by temperature-stimulus at the current
    current position at the current time: b(T(x,t)).

    TODO: implement, this should output Bias + Force?
    """
    return 0


def MassAgent(init_state, t):
    """
    The right-hand side of the damped oscillator ODE
    (d^2x/dt^2) = ( 2*zeta*w0*(dx/dt) + w0^2*x ) / m

    TODO: why does this fxn need the time vector? it doesn't seem to use it.
        or is it because we will need it later for the driving forces..? -rd
    """
    #This function gets entered into the ode, which is time-dependent.
    x, dxdt = init_state[0], init_state[1]
    #y, dydt = y0[0], y0[1] #starting to think about 2D..
    
    #originally p = dx/dt, this was modified to include timesetp values
    #i feel like user-defined dt should be in the equations below...not sure -sz
    dxddt = (-2 * zeta * w0 * dxdt - w0**2 * x + 5*baselineDrivingForce() + biasedDrivingForce()) / m 

    return [dxdt, dxddt]

# TODO: change the ode such that if zeta is an n x 1 array, it produces n solution arrays

"""
odeint basically works like this:
1) calc state derivative xdd and xd at t=0 given initial states (x, xd)
2) estimate x(t) using x(t-dt), xd(t-dt), xdd(t-dt)
3) then calc xdd(t+dt) using that x(t = t+dt) and xd(t = t+dt)
4) iterate steps 2 and 3 to calc subsequent timesteps, using the x, xd, xdd
    from the previous dt to calculate the state values for the current dt
...

then, it outputs the system states [x, xd](t)
"""
states1 = odeint(MassAgent, x0, t)

fig, ax = plt.plot(t, states1)
plt.xlabel('time')
plt.ylabel('states')
plt.title('mass-agent oscillating system')
plt.legend(('$x$', '$\dot{x}$'))


def StateSpaceAnim():
    """Animation of changes in state-space over time.

    Credit to Paul Gribble (email: paul [at] gribblelab [dot] org), code based
    on a function in his "Computational Modelling in Neuroscience" course:
    http://www.gribblelab.org/compneuro/index.html
    """
    plt.figure()
    pb, = plt.plot(states1[:, 0], states1[:, 1], 'b-', alpha=0.2)
    plt.xlabel('$x$')
    plt.ylabel('$\dot{x}$')
    p, = plt.plot(states1[0:10, 0], states1[0:10, 1], 'b-')
    pp, = plt.plot(states1[10, 0], states1[10, 1], 'b.', markersize=10)
    tt = plt.title("%4.2f sec" % 0.00)

    # animate
    step = 2
    for i in xrange(1, np.shape(states1)[0]-10, step):
        p.set_xdata(states1[10+i:20+i, 0])
        p.set_ydata(states1[10+i:20+i, 1])
        pp.set_xdata(states1[10+i, 0])
        pp.set_ydata(states1[10+i, 1])
        tt.set_text("State-space trajectory animation - step # %d" % (i))
        plt.draw()

#tateSpaceAnim()
