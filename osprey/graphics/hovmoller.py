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
              varlabel, 
              timeoff=0,
              rescaled=False, 
              reader='nemo',
              replace=False, 
              metric='base', 
              avetype='moving'): 
    """ 
    Plot of Hovmöller diagram 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    timeoff: time offset
    color: curve color
    rescaled: rescale field by the initial value at time=0
    reader: read the original raw data or averaged data ['nemo', 'post']
    metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    avetype: choose the type of avereage ['moving' or 'standard']
    
    """
    

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
        data = postreader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname='hovmoller', replace=replace, metric=metric)
        tvec = data['time'].values.flatten()
    zvec = data['z'].values.flatten()

    # fixing variable x-axis
    if avetype == 'moving':
        if reader == 'nemo':
            vec = movave(spacemean(data, varname, '2D', ztag),12)
        elif reader == 'post':
            vec = movave(data[varlabel],12)
    elif avetype == 'standard':
        vec = data[varname].values.flatten()
    
    if rescaled == True:
        hovm = (data[varname] - data[varname].isel(time=0))
    
    # plot
    pp = hovm.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.xlabel('time')
    plt.ylabel('depth')

    return pp

