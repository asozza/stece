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


def hovmoller(expname, 
              startyear, endyear, 
              varlabel, 
              color=None, 
              reader="nemo", 
              metric="base", 
              avetype="moving"): 
    """ Function for plotting Hövmoller diagrams """
    
    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    info = vardict('nemo')[varname]

    # reading data
    if reader == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        tvec = get_decimal_year(data['time'].values)
    elif reader == "post":
        data = postreader_averaged(expname, startyear, endyear, varlabel, 'timeseries', metric)
        tvec = data['time'].values.flatten()       
    zvec = data['z'].values.flatten()

    # fixing variable x-axis
    vec = data[varname].values.flatten()
    if avetype == 'moving':
        vec = spacemean(data, varname, '2D', ztag)
    vec_cost = cost(vec, cost_value, cost_type)

    delta = (data[var] - data[var].isel(time=0))
    pp = delta.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data['z'].long_name)

    return pp

