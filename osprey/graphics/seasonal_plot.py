#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for Seasonal plots

Author: Alessandro Sozza (CNR-ISAC) 
Date: Sept 2024
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
from osprey.utils.time import get_decimal_year
from osprey.means.means import movave
from osprey.means.means import cost
from osprey.means.means import spacemean
from osprey.utils.vardict import vardict


def seasonal_plot(expname, 
                startyear, endyear, 
                var,                 
                cost_value=1, 
                offset=0, 
                color=None,
                rescaled=False,
                reader_type="nemo", 
                cost_type="norm", 
                average_type="moving"):               
    """ Function for seasonal plots """
    
    # reading data
    if reader_type == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        tvec = get_decimal_year(data['time'].values)

    elif reader_type == "averaged":
        data = postreader_nemo(expname, startyear, endyear, var, 'series')
        tvec = data['time'].values.flatten()

    # fix time-axis
    tvec_cutted = tvec[6:-6]
    tvec_offset = [tvec_cutted[i]+offset for i in range(len(tvec_cutted))]

    # y-axis
    vec = data[var].values.flatten()
    if average_type == 'moving':
        ndim = vardict('nemo')[var]
        vec_x = movave(spacemean(data, var_x, ndim),12)
        vec_y = movave(spacemean(data, var_y, ndim),12)    
    vec_cutted = vec[6:-6]

    # apply cost function
    vec_cost = cost(vec_cutted, cost_value, cost_type) 

    # apply rescaling
    if rescaled == True:
        vec_cost = vec_cost/vec_cost[0]

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color

    pp = plt.plot(tvec_offset, vec_cost, **plot_kwargs)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[var].long_name)

    return pp


