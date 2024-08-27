#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for Hovmoller diagrams 

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC) 
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
from osprey.utils.time import get_decimal_year
from osprey.means.means import cost
from osprey.means.means import spacemean
from osprey.utils.vardict import vardict


def hovmoller_plot(expname, 
            startyear, endyear, 
            var, 
            cost_value=1, 
            color=None, 
            reader_type="output", 
            cost_type="norm", 
            average_type="moving"): 
    """ Function for drawing Hövmoller diagrams """
    
    # reading data
    if reader_type == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        tvec = get_decimal_year(data['time'].values)
    elif reader_type == "averaged":
        data = postreader_averaged(expname, startyear, endyear, var, 'series')
        tvec = data['time'].values.flatten()
    zvec = data['z'].values.flatten()

    # fixing variable x-axis
    vec = data[var].values.flatten()
    if average_type == 'moving':
        ndim = vardict('nemo')[var]
        vec = spacemean(data, var, '2D')
    vec_cost = cost(vec, cost_value, cost_type)

    delta = (data[var] - data[var].isel(time=0))
    pp = delta.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data['z'].long_name)

    return pp

