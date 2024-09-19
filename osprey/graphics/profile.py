#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for profiles

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC) 
Date: Mar 2024
"""

import os
import numpy as np
import xarray as xr
import dask
import cftime
#import nc_time_axis
import matplotlib.pyplot as plt

from osprey.actions.reader import reader_nemo
from osprey.actions.postreader import postreader_nemo
from osprey.means.means import cost
from osprey.means.means import globalmean
from osprey.utils.vardict import vardict

def _rescaled(vec):
    """ rescale by the initial value """
    return vec/vec[0]

def profile(expname, startyear, endyear, varlabel, 
            reader="post", metric="base", replace=False, rescale=False, 
            color=None, linestyle='-', marker=None, label=None, figname=None):
    """ 
    Graphics of averaged vertical profile 
    
    Positional Args:
    - expname: experiment name
    - startyear,endyear: time window
    - varlabel: variable label (varname + ztag)

    Optional Args:
    - reader: read the original raw data or averaged data ['nemo', 'post']
    - metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    - replace: replace existing files [False or True]
    
    Optional Args for figure settings:
    - rescale: rescale by initial value
    - color, linestyle, marker, label: plot attributes
    - figname: save plot to file

    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    info = vardict('nemo')[varname]

    # Read data from raw NEMO output
    if reader == 'nemo':
        data = reader_nemo(expname=expname, startyear=startyear, endyear=endyear)
        vec = globalmean(data, varname, '2D')

    # Read data from post-processed data
    elif reader == 'post':
        data = postreader_nemo(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname='profile', replace=replace, metric=metric)
        vec=data[varname].values.flatten()

    # fixing depth y-axis
    zvec = data['z'].values.flatten()

    # plot
    plot_kwargs = {}
    if color:
        plot_kwargs['color'] = color
    if linestyle:
        plot_kwargs['linestyle'] = linestyle
    if marker:
        plot_kwargs['marker'] = marker
    if label:
        plot_kwargs['label'] = label

    pp = plt.plot(vec, -zvec, **plot_kwargs)
    plt.xlabel(info['long_name'])
    plt.ylabel('depth')

    return pp

def profile_two(expname1, startyear1, endyear1, 
                expname2, startyear2, endyear2, varlabel,  
                reader="post", metric="base", replace=False, rescale=False, 
                color=None, linestyle='-', marker=None, label=None, figname=None):        
    """ 
    Graphics of two-experiment vertical profile distance based on metric 
    
    Positional Args:
    - expname: experiment name
    - startyear,endyear: time window
    - varlabel: variable label (varname + ztag)

    Optional Args:
    - reader: read the original raw data or averaged data ['nemo', 'post']
    - metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    - replace: replace existing files [False or True]
    
    Optional Args for figure settings:
    - rescale: rescale by initial value
    - color, linestyle, marker, label: plot attributes
    - figname: save plot to file
    
    """
    
    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    info = vardict('nemo')[varname]
    
    # reading data
    if reader == 'nemo':
        data1 = reader_nemo(expname=expname1, startyear=startyear1, endyear=endyear1)
        data2 = reader_nemo(expname=expname2, startyear=startyear2, endyear=endyear2)
        vec1 = globalmean(data1, varname, '2D')
        vec2 = globalmean(data2, varname, '2D')

    elif reader == 'post':
        data1 = postreader_nemo(expname=expname1, startyear=startyear1, endyear=endyear1, varlabel=varlabel, diagname='profile', replace=replace, metric=metric)
        data2 = postreader_nemo(expname=expname2, startyear=startyear2, endyear=endyear2, varlabel=varlabel, diagname='profile', replace=replace, metric=metric)
        vec1 = data1[varname].values.flatten()
        vec2 = data2[varname].values.flatten()

    # depth y-axis 
    zvec = data1['z'].values.flatten()

    # apply cost function
    vec_cost = cost(vec1, vec2, metric)

    # plot
    plot_kwargs = {}
    if color:
        plot_kwargs['color'] = color
    if linestyle:
        plot_kwargs['linestyle'] = linestyle
    if marker:
        plot_kwargs['marker'] = marker
    if label:
        plot_kwargs['label'] = label

    pp = plt.plot(vec_cost, -zvec, **plot_kwargs)
    plt.xlabel(info['long_name'])
    plt.ylabel('depth')

    return pp