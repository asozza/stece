#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for Gregory plots

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
from osprey.means.means import movave
from osprey.means.means import cost
from osprey.means.means import spacemean
from osprey.utils.vardict import vardict


def gregory_plot(expname, 
                startyear, endyear, 
                varname1, 
                varname2,
                color=None,
                reader='nemo',
                replace=False, 
                metric='base', 
                avetype='moving'):               
    """ 
    Gregory Plot
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varname_{1,2}: variable names
    color: curve color
    reader: read the original raw data or averaged data ['nemo', 'post']
    replace: substitute existing files
    metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    avetype: choose the type of avereage ['moving' or 'standard']
         
    """

    info1 = vardict('nemo')[varname1]
    info2 = vardict('nemo')[varname2]

    # reading data
    if reader == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        tvec = get_decimal_year(data['time'].values)
    elif reader == "post":
        data1 = postreader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varname1, diagname='timeseries', replace=replace, metric=metric)
        data2 = postreader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varname2, diagname='timeseries', replace=replace, metric=metric)
        tvec = data1['time'].values.flatten()
    tvec_cutted = tvec[6:-6]

    # y-axis    
    if avetype == 'moving':
        if reader == 'nemo':
            vec1 = movave(spacemean(data, varname1, info1['dim']),12)
            vec2 = movave(spacemean(data, varname2, info2['dim']),12)
        elif reader == 'post':
            vec1 = movave(data1[varname1],12)
            vec2 = movave(data2[varname2],12)
    elif avetype == 'standard':
        vec1 = data[varname1].values.flatten()
        vec2 = data[varname1].values.flatten()
    vec1_cutted = vec1[6:-6]
    vec2_cutted = vec2[6:-6]

    # plot (add palette according to time?)
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color

    pp = plt.plot(vec1_cutted, vec2_cutted, **plot_kwargs)
    plt.xlabel(info1['long_name'])
    plt.ylabel(info2['long_name'])

    return pp


