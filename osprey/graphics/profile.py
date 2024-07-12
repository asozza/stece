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
            var, cost_value, 
            color, 
            reader_type="output", 
            cost_type="norm", 
            average_type="moving"): 
    """ Graphics of vertical profile """
    
    if reader_type == 'output':
        data = reader_nemo(expname, startyear, endyear)
    elif reader_type == 'averaged':
        data = postreader_averaged(expname, startyear, endyear, var, 'profile')
        
    zvec = data['z'].values.flatten()

    vec = data[var].values.flatten()
    if average_type == 'moving':
        ndim = vardict('nemo')[var]
        vec = globalmean(data, var, '2D')

    pp = plt.plot(cost(vec, cost_value, cost_type), -zvec, color)
    plt.xlabel(data[var].long_name)
    plt.ylabel(data['z'].long_name)

    return pp
