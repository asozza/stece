#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for Hovmöller diagrams 

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC) 
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
from osprey.means.means import spacemean
from osprey.utils.vardict import vardict

def _rescaled(vec):
    """ rescale by the initial value """
    return vec/vec.isel(time=0)

def hovmoller(expname, startyear, endyear, varname, 
              reader="post", metric="base", replace=False, rescale=False, figname=None):
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
    - rescale: rescale by initial value
    - figname: save plot to file
    
    """
    
    info = vardict('nemo')[varname]

    # Read data from raw NEMO output
    if reader == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        vec = spacemean(data, varname, '2D')

    # Read post-processed data
    elif reader == "post":
        data = postreader_nemo(expname=expname, startyear=startyear, endyear=endyear, varlabel=varname, diagname='hovmoller', replace=replace, metric=metric)
        vec = data[varname]

    # apply rescaling
    if rescale:
        vec = _rescaled(vec)
    
    # plot
    pp = vec.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.xlabel('time')
    plt.ylabel('depth')
    plt.ylim(0,5000)
    plt.gca().invert_yaxis() # invert y-axis

    return pp

