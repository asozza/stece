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
from osprey.means.means import spacemean, timemean
from osprey.utils import catalogue


def map(expname, startyear, endyear, varlabel, format="global", reader="post", orca="ORCA2",
        replace=False, metric="base", refinfo=None, rescale=False, ax=None, figname=None):
    """ 
    Horizontal Map
    
    Positional Args:
    - expname: experiment name
    - startyear,endyear: time window
    - varlabel: variable name + ztag

    Optional Args:
    - format: time format [global, winter, spring, summer, autumn]
    - reader: read the original raw data or averaged data ['nemo', 'post']
    - orca: ORCA configuration [ORCA2, eORCA1]
    - replace: replace existing files [False or True]
    - metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    - refinfo: reference information
    - rescale: rescale by initial value: False or true?
    
    Optional Args for figure settings:
    - color: color?
    - ax: axes for subplots
    - figname: save plot to file
    
    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname, ztag = varlabel, None
    
    info = catalogue.observables('nemo')[varname]

    # Read data from raw NEMO output
    if reader == "nemo":


        data = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)        
        data = averaging(data=data, varlabel=varlabel, diagname='map', format=format, orca=orca)
                    
    # Read post-processed data
    elif reader == "post":

        data = postreader_nemo(expname=expname, startyear=startyear, endyear=endyear, varlabel=varname, diagname='map', replace=replace, metric=metric)
        data = data[varname]
    
    # plot
    pp = data.plot(x='x', y='y', cmap=plt.cm.coolwarm)

    return pp

