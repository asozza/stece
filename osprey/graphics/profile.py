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
from osprey.actions.post_reader import postreader_averaged
from osprey.means.means import cost
from osprey.means.means import globalmean
from osprey.utils.vardict import vardict


def profile(expname, 
            startyear, endyear, 
            varlabel, 
            color=None, 
            rescaled=False, 
            reader='nemo',
            replace=False,
            metric='base'): 
    """ 
    Graphics of averaged vertical profile 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    color: curve color
    rescaled: rescale timeseries by the initial value at time=0
    reader: read the original raw data or averaged data ['nemo', 'post']
    replace: replace existing file
    metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    avetype: choose the type of avereage ['moving' or 'standard']

    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    info = vardict('nemo')[varname]

    # reading data
    if reader == 'nemo':
        data = reader_nemo(expname=expname, startyear=startyear, endyear=endyear)
        vec = globalmean(data, varname, '2D')
    elif reader == 'post':
        data = postreader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname='profile', replace=replace, metric=metric)
        vec=data[varname].values.flatten()

    # fixing depth y-axis
    zvec = data['z'].values.flatten()

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color

    pp = plt.plot(vec, -zvec, **plot_kwargs)
    plt.xlabel(info['long_name'])
    plt.ylabel('depth')

    return pp

def profile_two(expname1, expname2, 
                startyear1, endyear1, 
                startyear2, endyear2,             
                varlabel, 
                color=None, 
                rescaled=False,
                reader='nemo',
                replace=False,
                metric='base',
                avetype='moving'): 
    """ 
    Graphics of two-experiment vertical profile distance based on metric 
    
    Args:
    expname_1,2: experiment names
    startyear,endyear_1,2: time windows
    varlabel: variable label (varname + ztag)
    color: curve color
    rescaled: rescale timeseries by the initial value at time=0
    reader: read the original raw data or averaged data ['nemo', 'post']
    replace: replace existing file
    metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    avetype: choose the type of avereage ['moving' or 'standard']
    
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
    elif reader == 'post':
        data1 = postreader_averaged(expname=expname1, startyear=startyear1, endyear=endyear1, varlabel=varlabel, diagname='profile', replace=replace, metric=metric)
        data2 = postreader_averaged(expname=expname2, startyear=startyear2, endyear=endyear2, varlabel=varlabel, diagname='profile', replace=replace, metric=metric)

    # depth y-axis 
    zvec = data1['z'].values.flatten()

    # variable x-axis
    if avetype == 'moving':
        vec1 = globalmean(data1, varname, '2D')
        vec2 = globalmean(data2, varname, '2D')
    elif avetype == 'standard':
        vec1 = data1[varname].values.flatten()
        vec2 = data2[varname].values.flatten()

    # apply cost function
    vec_cost = cost(vec1, vec2, metric)

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color

    pp = plt.plot(vec_cost, -zvec, **plot_kwargs)
    plt.xlabel(info['long_name'])
    plt.ylabel('depth')

    return pp