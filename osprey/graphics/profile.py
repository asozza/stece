#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for profiles

Author: Alessandro Sozza (CNR-ISAC) 
Date: Mar 2024
"""

import os
import numpy as np
import xarray as xr
import dask
import cftime
import nc_time_axis
import matplotlib.pyplot as plt

from osprey.actions.reader import reader_nemo
from osprey.actions.post_reader import postreader_averaged
from osprey.means.means import cost
from osprey.means.means import globalmean
from osprey.utils.vardict import vardict


def profile(expname, 
            startyear, endyear, 
            var, 
            cost_value=1, 
            color=None, 
            reader_type="output", 
            cost_type="norm", 
            average_type="moving"): 
    """ Graphics of vertical profile """
    
    # reading data
    if reader_type == 'output':
        data = reader_nemo(expname, startyear, endyear)
    elif reader_type == 'averaged':
        data = postreader_averaged(expname, startyear, endyear, var, 'profile')
    
    # fixing depth y-axis
    zvec = data['z'].values.flatten()

    # fixing variable x-axis
    vec = data[var].values.flatten()
    if average_type == 'moving':
        ndim = vardict('nemo')[var]
        vec = globalmean(data, var, '2D')
    vec_cost = cost(vec, cost_value, cost_type)

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color

    pp = plt.plot(vec_cost, -zvec, **plot_kwargs)
    plt.xlabel(data[var].long_name)
    plt.ylabel(data['z'].long_name)

    return pp

def profile_diff(expname1, expname2, 
            startyear, endyear, 
            var, 
            cost_value=1, 
            color=None, 
            reader_type="output", 
            cost_type="norm", 
            average_type="moving"): 
    """ Graphics of vertical profile """
    
    # reading data
    if reader_type == 'output':
        data1 = reader_nemo(expname1, startyear, endyear)
        data2 = reader_nemo(expname2, startyear, endyear)
    elif reader_type == 'averaged':
        data1 = postreader_averaged(expname1, startyear, endyear, var, 'profile')
        data2 = postreader_averaged(expname2, startyear, endyear, var, 'profile')


    # depth y-axis 
    zvec = data1['z'].values.flatten()

    # variable x-axis
    vec1 = data1[var].values.flatten()
    vec2 = data2[var].values.flatten()
    if average_type == 'moving':
        ndim = vardict('nemo')[var]
        vec1 = globalmean(data1, var, '2D')
        vec2 = globalmean(data2, var, '2D')

    # apply cost function
    vec_cost = cost(vec1, vec2, cost_type)

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color

    pp = plt.plot(vec_cost, -zvec, **plot_kwargs)
    plt.xlabel(data1[var].long_name)
    plt.ylabel(data1['z'].long_name)

    return pp