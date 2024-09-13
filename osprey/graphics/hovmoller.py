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
from osprey.actions.post_reader import postreader_averaged
from osprey.utils.time import get_decimal_year
from osprey.means.means import cost, movave
from osprey.means.means import spacemean
from osprey.utils.vardict import vardict


def hovmoller(expname, 
              startyear, endyear, 
              varname,
              rescaled=False, 
              reader='nemo',
              replace=False, 
              metric='base'): 
    """ 
    Plot of Hovmöller diagram 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varname: variable name
    rescaled: rescale field by the initial value at time=0
    reader: read the original raw data or averaged data ['nemo', 'post']
    metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    
    """
    
    info = vardict('nemo')[varname]

    # reading data
    if reader == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        vec = spacemean(data, varname, '2D')
    elif reader == "post":
        data = postreader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varname, diagname='hovmoller', replace=replace, metric=metric)
        vec = data[varname]

    if reader == 'nemo':
        if metric != 'base':
        # read from yaml file
        local_paths = paths()
        filename = os.path.join(local_paths['osprey'], 'meanfield.yaml')
        with open(filename) as yamlfile:
            config = yaml.load(yamlfile, Loader=yaml.FullLoader)    
        if 'meanfield' in config:
            meanfield = config['meanfield']
            exp0 = meanfield[0]['expname']
            y0 = meanfield[1]['startyear']
            y1 = meanfield[2]['endyear']
        mdata = reader_averaged(expname=exp0, startyear=y0, endyear=y1, varlabel=varlabel, diagname='field', metric='base')
        ydata = cost(xdata, mdata, metric)
    elif reader == 'post':
        #
        data = 1.0

    if rescaled == True:
        hovm = (vec -vec.isel(time=0))
    else:
        hovm = vec
    
    # plot
    pp = hovm.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.xlabel('time')
    plt.ylabel('depth')
    plt.ylim(0,5000)
    plt.gca().invert_yaxis() # invert y-axis

    return pp

