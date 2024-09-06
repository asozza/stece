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
               cost_value=1, 
               offset=0, 
               color=None, 
               rescaled=False, 
               reader_type="nemo", 
               cost_type="norm", 
               average_type="moving"): 
    """ 
    Graphics of timeseries 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + subregion)
    cost_value: ?
    offset: time offset
    color: curve color
    rescaled: rescale timeseries by the initial value at time=0
    reader_type: read the original raw data or averaged data [nemo, post]
    cost_type: choose the type of cost function [norm, diff, rdiff, abs, rel, var, rvar] 
    
    """
    
    if '-' in varlabel:
        varname, subregion = varlabel.split('-', 1)
    else:
        varname=varlabel
        subregion=None

    # reading data
    if reader_type == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        tvec = get_decimal_year(data['time'].values)
    elif reader_type == "post":
        data = postreader_averaged(expname, startyear, endyear, varlabel, 'timeseries')
        tvec = data['time'].values.flatten()

    # fix time-axis
    tvec_cutted = tvec[6:-6]
    tvec_offset = [tvec_cutted[i]+offset for i in range(len(tvec_cutted))]

    # y-axis
    vec = data[varlabel].values.flatten()
    if average_type == 'moving':
        if reader_type == 'nemo':
            ndim = vardict('nemo')[varname]
            vec = movave(spacemean(data, varname, ndim, subregion),12)
        elif reader_type == 'post':
            vec = movave(data[varlabel],12)
    vec_cutted = vec[6:-6]

    # apply cost function
    vec_cost = cost(vec_cutted, cost_value, cost_type) 

    # apply rescaling
    if rescaled == True:
        vec_cost = vec_cost/vec_cost[0]

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color

    pp = plt.plot(tvec_offset, vec_cost, **plot_kwargs)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[varlabel].long_name)

    return pp


def timeseries_diff(expname1, expname2, 
                    startyear, endyear, 
                    varlabel, 
                    offset=0, 
                    color=None,
                    rescaled=False,
                    reader_type="nemo",
                    cost_type="norm", 
                    average_type="moving"): 
    """ 
    Graphics of two-field difference timeseries 
    
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
        varname, subregion = varlabel.split('-', 1)
    else:
        varname=varlabel
        subregion=None

    # reading data
    if reader_type == 'nemo':
        data1 = reader_nemo(expname1, startyear, endyear)
        data2 = reader_nemo(expname2, startyear, endyear)
        tvec = get_decimal_year(data1['time'].values)
    elif reader_type == 'averaged':
        data1 = postreader_averaged(expname1, startyear, endyear, varlabel, 'series')
        data2 = postreader_averaged(expname2, startyear, endyear, varlabel, 'series')        
        tvec = data1['time'].values.flatten()

    # fix time axis
    tvec_cutted = tvec[6:-6]
    tvec_offset = [tvec_cutted[i]+offset for i in range(len(tvec_cutted))]

    # fix y-axis
    vec1 = data1[varname].values.flatten()
    vec2 = data1[varname].values.flatten()
    if average_type == 'moving':
        if reader_type == 'nemo':
            ndim = vardict('nemo')[varname]
            vec1 = movave(spacemean(data1, varname, ndim, subregion),12)
            vec2 = movave(spacemean(data2, varname, ndim, subregion),12)
        elif reader_type == 'post':
            vec1 = movave(data1[varlabel],12)
            vec2 = movave(data2[varlabel],12)            
    vec1_cutted = vec1[6:-6]
    vec2_cutted = vec2[6:-6]
    vec_cost = cost(vec1_cutted, vec2_cutted, cost_type)

    # apply rescaling
    if rescaled == True:
        vec_cost = vec_cost/vec_cost[0]

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color
    
    pp = plt.plot(tvec_offset, vec_cost, **plot_kwargs)
    plt.xlabel(data1['time'].long_name)
    plt.ylabel(data1[varlabel].long_name)

    return pp


def timeseries_diff_mf(expname1, 
                       startyear1, endyear1, 
                       expname2, 
                       startyear2, endyear2, 
                       varlabel, 
                       offset=0, 
                       color=None, 
                       rescaled=False, 
                       reader_type="nemo", 
                       cost_type="norm", 
                       average_type="moving"):
    """ 
    Graphics of mean-field difference timeseries 
        
    Args:
    expname 1,2: experiment name
    startyear,endyear 1,2: time window
    varlabel: variable label (varname + subregion)    
    offset: time offset
    color: curve color
    rescaled: rescale timeseries by the initial value at time=0
    reader_type: read the original raw data or averaged data [nemo, post]
    cost_type: choose the type of cost function [norm, diff, rdiff, abs, rel, var, rvar]
    
    """


    if '-' in varlabel:
        varname, subregion = varlabel.split('-', 1)
    else:
        varname=varlabel
        subregion=None

    # reading data
    if reader_type == 'nemo':
        data1 = reader_nemo(expname1, startyear1, endyear1)
        data2 = reader_nemo(expname2, startyear2, endyear2)
        tvec = get_decimal_year(data1['time'].values)
        meanfld = timemean(data2, varname)
            
    elif reader_type == 'averaged':
        data1 = postreader_averaged(expname1, startyear1, endyear1, varlabel, 'timeseries')
        meanfld = postreader_averaged(expname2, startyear2, endyear2, varlabel, 'field')        
        tvec = data1['time'].values.flatten()

    fdata = cost(data1, meanfld, cost_type)
    fdata.attrs['name'] = data1.attrs['name']

    # fix time axis
    tvec_cutted = tvec[6:-6]
    tvec_offset = [tvec_cutted[i]+offset for i in range(len(tvec_cutted))]

    # select y-axis    
    if average_type == 'moving':
        
        if reader_type == 'nemo':
            ndim = vardict('nemo')[varname]
            vec_cost = movave(spacemean(fdata, varname, ndim, subregion),12)
        
        elif reader_type == 'post':
            vec_cost = movave(fdata[varlabel],12)
    
    elif average_type == 'standard':
        vec_cost = fdata[varname].values.flatten()  

    # apply rescaling
    if rescaled == True:
        vec_cost = vec_cost/vec_cost[0]
    
    # fix y-axis
    vec_cutted = vec_cost[6:-6]

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color
    
    pp = plt.plot(tvec_offset, vec_cutted, **plot_kwargs)
    plt.xlabel(data1['time'].long_name)
    plt.ylabel(data1[varlabel].long_name)

    return pp