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

from osprey.actions.post_reader import postreader_averaged
from osprey.means.means import movave
from osprey.means.means import cost

def timeseries(expname, startyear, endyear, var, ndim, norm, idx_norm, idx_ave, offset, color):
    """ graphics of timeseries """

    å# read (or create) averaged data
    data = postreader_averaged(expname, startyear, endyear, var, ndim, 'series')
    # assembly and plot
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = movave(data[var].values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, cost(vv1, norm, idx_norm), color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[var].long_name)

    return pp

