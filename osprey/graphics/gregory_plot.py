#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for Gregory plots

Author: Alessandro Sozza (CNR-ISAC) 
Date: Mar 2024
"""

import os
import numpy as np
import xarray as xr
import dask
import cftime
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from osprey.actions.reader import reader_nemo
from osprey.actions.postreader import postreader_nemo
from osprey.utils.time import get_decimal_year
from osprey.utils.folders import paths
from osprey.means.means import movave
from osprey.means.means import cost
from osprey.means.means import spacemean
from osprey.utils.vardict import vardict

def _cutted(vec):
    """ Cut vector """
    return vec[6:-6]

def _rescaled(vec):
    """ rescale by the initial value """
    return vec/vec[0]

def gregory_plot(expname, startyear, endyear, varname1, varname2, 
                 reader="post", metric="base", replace=False, rescale=False, avetype="moving", 
                 color=None, linestyle='-', marker=None, label=None, figname=None):
    """ 
    Gregory Plot

    Positional Args:
    - expname: experiment name
    - startyear,endyear: time window
    - varname1,varname2: variable names

    Optional Args:
    - reader: read the original raw data or averaged data ['nemo', 'post']
    - metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    - replace: replace existing files [False or True]
    
    Optional Args for figure settings:
    - rescale: rescale by initial value
    - avetype: choose the type of average ['moving' or 'standard']   
    - color, linestyle, marker, label: plot attributes
    - figname: save plot to file
         
    """

    info1 = vardict('nemo')[varname1]
    info2 = vardict('nemo')[varname2]

    # Read data from raw NEMO output
    if reader == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        tvec = get_decimal_year(data['time'].values)

        # apply moving average
        if avetype == 'moving':
            vec1 = movave(spacemean(data, varname1, info1['dim']),12)
            vec2 = movave(spacemean(data, varname2, info2['dim']),12)
            tvec, vec1, vec2 = _cutted(tvec), _cutted(vec1), _cutted(vec2)
        else:
            vec1 = data[varname1].values.flatten()
            vec2 = data[varname1].values.flatten()            

    # Read post-processed data
    elif reader == "post":
        data1 = postreader_nemo(expname=expname, startyear=startyear, endyear=endyear, varlabel=varname1, diagname='timeseries', replace=replace, metric=metric)
        data2 = postreader_nemo(expname=expname, startyear=startyear, endyear=endyear, varlabel=varname2, diagname='timeseries', replace=replace, metric=metric)
        tvec = data1['time'].values.flatten()

        # apply moving average
        if avetype == 'moving':
            vec1 = movave(data1[varname1],12)
            vec2 = movave(data2[varname2],12)
            tvec, vec1, vec2 = _cutted(tvec), _cutted(vec1), _cutted(vec2)
        else:
            vec1 = data[varname1].values.flatten()
            vec2 = data[varname1].values.flatten()


    # markers
    years_interval = 120 # number of months x years of one chunk
    time_indices = np.arange(0, len(tvec), years_interval)    
    vec1_markers = vec1[time_indices]
    vec2_markers = vec2[time_indices]

    # plot
    plot_kwargs = {}
    if color:
        plot_kwargs['color'] = color
    if linestyle:
        plot_kwargs['linestyle'] = linestyle
    if label:
        plot_kwargs['label'] = label

    scatter_kwargs = {}
    if color:
        scatter_kwargs['color'] = color
    if marker:
        scatter_kwargs['marker'] = marker

    fig = plt.subplot()

    plt.plot(vec1, vec2, **plot_kwargs)
    plt.scatter(vec1_markers, vec2_markers, zorder=10, edgecolor='black', label='_nolegend_', **scatter_kwargs)

    # Set labels, example labels here
    plt.xlabel(info1['long_name'])
    plt.ylabel(info2['long_name'])

    # Save figure
    if figname:
        dirs = paths()
        plt.savefig(os.path.join(dirs['osprey'], figname))

    return fig

