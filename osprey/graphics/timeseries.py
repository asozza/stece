#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for timeseries

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


def timeseries(expname, startyear, endyear, var, ndim, norm, idx_norm, idx_ave, offset, color):
    """ graphics of timeseries """

    isub = False
    if '-' in var:
        isub = True

    # read (or create) averaged data
    data = osi.read_averaged_timeseries_T(expname, startyear, endyear, var, ndim, isub)
    # assembly and plot
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = osm.movave(data[var].values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, osm.cost(vv1, norm, idx_norm), color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[var].long_name)

    return pp


def timeseries_diff(exp1, exp2, startyear, endyear, var, ndim, norm, idx_norm, idx_ave, offset):
    """ graphics of timeseries of two-field difference """

    isub = False
    if '-' in var:
        isub = True
        
    # read (or create) averaged data 
    data1 = osi.read_averaged_timeseries_T(exp1, startyear, endyear, var, ndim, isub)
    data2 = osi.read_averaged_timeseries_T(exp2, startyear, endyear, var, ndim, isub)
    # assembly and plot
    tt = data1['time'].values.flatten()
    delta = data2[var]-data1[var]
    if idx_ave == 'ave':
        vv = delta.values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = osm.movave(delta.values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2,osm.cost(vv1, norm, idx_norm))
    plt.xlabel(data1['time'].long_name)
    plt.ylabel(data1[var].long_name)

    return pp


def timeseries_diff2(expname, startyear, endyear, refname, startref, endref, var, ndim, idx_norm, idx_ave, offset, color):

    isub = False
    if '-' in var:
        isub = True

    # read (or create) averaged data 
    data = osi.read_averaged_timeseries_T(expname, startyear, endyear, var, ndim, isub)    
    mdata = osi.read_averaged_field_T(refname, startref, endref, var, ndim)

    # assembly and plot
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        vm = osm.spacemean(expname, mdata[var], ndim)
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = osm.movave(data[var].values.flatten(),12)
        vm = osm.spacemean(expname, mdata[var], ndim)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, osm.cost(vv1, vm, idx_norm), color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel('Cost function')

    return pp


def timeseries_anomaly(expname, startyear, endyear, refname, startref, endref, var, ndim, idx_ave, offset, color):

    data = osi.read_averaged_timeseries_local_anomaly_T(expname, startyear, endyear, refname, startref, endref, var, ndim)
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = osm.movave(data[var].values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, vv1, color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[var].long_name)

    return pp

