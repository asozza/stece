#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for timeseries

Author: Alessandro Sozza (CNR-ISAC) 
Date: Mar 2024
"""

import numpy as np
import xarray as xr
import dask
import cftime
import nc_time_axis
import matplotlib.pyplot as plt

from osprey.actions.reader import reader_nemo
from osprey.actions.post_reader import postreader_averaged
from osprey.utils.time import get_decimal_year
from osprey.means.means import movave
from osprey.means.means import cost
from osprey.means.means import spacemean
from osprey.utils.vardict import vardict


def timeseries(expname, 
               startyear, endyear, 
               var, subregion, cost_value, offset, 
               color, rescaled='False',
               reader_type="output", 
               cost_type="norm", 
               average_type="moving"): 
    """ Graphics of timeseries """
    
    if reader_type == 'output':
        data = reader_nemo(expname, startyear, endyear)
        tvec = get_decimal_year(data['time'].values)
    elif reader_type == 'averaged':
        data = postreader_averaged(expname, startyear, endyear, var, 'series')
        tvec = data['time'].values.flatten()

    vec = data[var].values.flatten()
    if average_type == 'moving':
        ndim = vardict('nemo')[var]
        vec = movave(spacemean(data, var, ndim, subregion),12)
    tvec_cutted = tvec[6:-6]; vec_cutted = vec[6:-6]
    tvec_offset = [tvec_cutted[i]+offset for i in range(len(tvec_cutted))]

    # rescaled
    if rescaled == 'True':
        # initial value
        vec_cutted = vec_cutted/vec_cutted[0]
        # final value?
        #vec_offset = vec_offset/vec_offset[-1]

    pp = plt.plot(tvec_offset, cost(vec_cutted, cost_value, cost_type), color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[var].long_name)

    return pp

