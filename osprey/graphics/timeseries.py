#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for timeseries

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC) 
Date: Mar 2024
"""

import numpy as np
import xarray as xr
import dask
import cftime
#import nc_time_axis
import matplotlib.pyplot as plt

from osprey.utils.time import get_decimal_year
from osprey.utils.vardict import vardict
from osprey.means.means import cost, movave
from osprey.means.means import spacemean, timemean
from osprey.actions.reader import reader_nemo
from osprey.actions.post_reader import postreader_averaged

def timeseries(expname, 
               startyear, endyear, 
               varlabel,
               timeoff=0, 
               color=None, 
               rescaled=False, 
               reader="nemo",
               replace=False, 
               metric="base",
               avetype="moving"): 
    """ 
    Graphics of timeseries 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    timeoff: time offset
    color: curve color
    rescaled: rescale timeseries by the initial value at time=0
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
        data = postreader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname='timeseries', replace=replace, metric=metric)
        tvec = data['time'].values.flatten()

    # fix time-axis
    tvec_cutted = tvec[6:-6]
    tvec_offset = [tvec_cutted[i]+timeoff for i in range(len(tvec_cutted))]

    # y-axis    
    if avetype == 'moving':
        if reader == 'nemo':
            vec = movave(spacemean(data, varname, info['dim'], ztag),12)
        elif reader == 'post':
            vec = movave(data[varlabel],12)
    elif avetype == 'standard':
        vec = data[varlabel].values.flatten()
    vec_cutted = vec[6:-6]

    # apply rescaling
    if rescaled == True:
        vec_cutted = vec_cutted/vec_cutted[0]

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color

    pp = plt.plot(tvec_offset, vec_cutted, **plot_kwargs)
    plt.xlabel('time')
    plt.ylabel(info['long_name'])

    return pp


def timeseries_diff(expname1, expname2, 
                    startyear, endyear, 
                    varlabel, 
                    offset=0, 
                    color=None,
                    rescaled=False,
                    reader="nemo",
                    replace=False,
                    metric="base", 
                    avetype="moving"): 
    """ 
    Graphics of two-experiment difference timeseries 
    
    Args:
    expname1,2: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + subregion)    
    offset: time offset
    color: curve color
    rescaled: rescale timeseries by the initial value at time=0
    reader_type: read the original raw data or averaged data [nemo, post]
    cost_type: choose the type of cost function [norm, diff, rdiff, abs, rel, var, rvar]
    
    """
    
    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    info = vardict('nemo')[varname]

    # reading data
    if reader == 'nemo':
        data1 = reader_nemo(expname1, startyear, endyear)
        data2 = reader_nemo(expname2, startyear, endyear)
        tvec = get_decimal_year(data1['time'].values)
    elif reader == 'averaged':
        data1 = postreader_averaged(expname=expname1, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname='timeseries', replace=replace, metric=metric)
        data2 = postreader_averaged(expname=expname2, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname='timeseries', replace=replace, metric=metric)
        tvec = data1['time'].values.flatten()

    # fix time axis
    tvec_cutted = tvec[6:-6]
    tvec_offset = [tvec_cutted[i]+offset for i in range(len(tvec_cutted))]

    # fix y-axis
    vec1 = data1[varname].values.flatten()
    vec2 = data1[varname].values.flatten()
    if avetype == 'moving':
        if reader == 'nemo':
            ndim = vardict('nemo')[varname]
            vec1 = movave(spacemean(data1, varname, info['dim'], ztag),12)
            vec2 = movave(spacemean(data2, varname, info['dim'], ztag),12)
        elif reader == 'post':
            vec1 = movave(data1[varlabel],12)
            vec2 = movave(data2[varlabel],12)            
    vec1_cutted = vec1[6:-6]
    vec2_cutted = vec2[6:-6]
    vec_cost = cost(vec1_cutted, vec2_cutted, metric)

    # apply rescaling
    if rescaled == True:
        vec_cost = vec_cost/vec_cost[0]

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color
    
    pp = plt.plot(tvec_offset, vec_cost, **plot_kwargs)
    plt.xlabel('time')
    plt.ylabel(info['long_name'])

    return pp
