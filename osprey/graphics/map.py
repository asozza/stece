#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for horizontal maps

Author: Alessandro Sozza (CNR-ISAC) 
Date: Mar 2024
"""

import os
import numpy as np
import xarray as xr
import dask
import cftime
import matplotlib.pyplot as plt

from osprey.actions.reader import reader_nemo
from osprey.actions.postreader import postreader_nemo
from osprey.utils.time import get_decimal_year
from osprey.means.means import cost, movave
from osprey.means.means import globalmean, spacemean, timemean
from osprey.utils.vardict import vardict


def map(expname, startyear, endyear, varname, reader="post", metric="base", replace=False, figname=None):
    """ 
    Plot of Hovmöller diagram 
    
    Positional Args:
    - expname: experiment name
    - startyear,endyear: time window
    - varname: variable name

    Optional Args:
    - reader: read the original raw data or averaged data ['nemo', 'post']
    - metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    - replace: replace existing files [False or True]
    
    Optional Args for figure settings:
    - figname: save plot to file
    
    """
    
    info = vardict('nemo')[varname]

    # Read data from raw NEMO output
    if reader == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        if info['dim'] == '2D':
            vec = timemean(data, varname)
        elif info['dim'] == '3D':
            vec = globalmean(data, varname, '1D')
        
    # Read post-processed data
    elif reader == "post":
        data = postreader_nemo(expname=expname, startyear=startyear, endyear=endyear, varlabel=varname, diagname='map', replace=replace, metric=metric)
        vec = data[varname]
    
    # plot
    pp = vec.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.xlabel('time')
    plt.ylabel('depth')
    plt.ylim(0,5000)
    plt.gca().invert_yaxis() # invert y-axis

    return pp

