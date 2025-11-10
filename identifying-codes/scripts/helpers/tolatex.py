# -*- coding: utf-8 -*-
"""
@time: 29/11/16 09:02 AM
@file: tolatex.py
@desc: copied from https://nipunbatra.github.io/blog/visualisation/2014/06/02/latexify.html
"""

from math import sqrt
import matplotlib

SPINE_COLOR = 'black'

def latexify(fig_width=None, fig_height=None, columns=1):
    """Set up matplotlib's RC params for LaTeX plotting.
    Call this before plotting a figure.

    Parameters
    ----------
    fig_width : float, optional, inches
    fig_height : float,  optional, inches
    columns : {1, 2}
    """

    # code adapted from http://www.scipy.org/Cookbook/Matplotlib/LaTeX_Examples

    # Width and max height in inches for IEEE journals taken from
    # computer.org/cms/Computer.org/Journal%20templates/transactions_art_guide.pdf

    assert(columns in [1,2])

    if fig_width is None:
        fig_width = 3.05 if columns==1 else 6.3 # width in inches

    if fig_height is None:
        golden_mean = (sqrt(5)-1.0)/2.0    # Aesthetic ratio
        fig_height = fig_width*golden_mean # height in inches

    print("fig_width:", fig_width)
    print("fig_height:", fig_height)

    MAX_HEIGHT_INCHES = 30.0
    MAX_HEIGHT_INCHES = 50.0
    if fig_height > MAX_HEIGHT_INCHES:
        print("WARNING: fig_height too large:" + fig_height +
              "so will reduce to" + MAX_HEIGHT_INCHES + "inches.")
        fig_height = MAX_HEIGHT_INCHES

    params = {'backend': 'ps',
              'text.latex.preamble': r'\usepackage{gensymb}',
              'axes.labelsize': 8, # fontsize for x and y labels (was 10)
              'axes.titlesize': 20,
              'font.size': 20, # was 10
              'legend.fontsize': 8, # was 10
              'xtick.labelsize': 8,
              'ytick.labelsize': 8,
              #'ytick.labelpos': right,
              'text.usetex': True,
              'figure.figsize': [fig_width,fig_height],
              'font.family': 'serif',
              'figure.dpi': 72.452830189
    }

    matplotlib.rcParams.update(params)

def format_axes(ax):

    for spine in ['left', 'top', 'right', 'bottom']:
        ax.spines[spine].set_color(SPINE_COLOR)
        ax.spines[spine].set_linewidth(0.5)

    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_tick_params(direction='in', color=SPINE_COLOR)
    ax.yaxis.set_tick_params(pad=2)
    return ax
