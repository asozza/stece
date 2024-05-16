#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GOAT: Global Ocean & Atmosphere Trends
------------------------------------------------------
GOAT library for graphics

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import os
import numpy as np
import xarray as xr
import dask
import matplotlib.pyplot as plt
import goat_tools as gt
import goat_io as io
import goat_means as gm

# time series:
# - can I add option to plot an portion of the existing averaged data?
# - can it be used to plot subvars like thetao-mix, thetao-pyc, thetao-aby?
# - add option for cost function anomaly with respect to a meanstate
def timeseries(expname, startyear, endyear, var, ndim, norm, idx_norm, idx_ave, offset, color):

    isub = False
    if '-' in var:
        isub = True

    # read (or create) averaged data 
    data = io.read_averaged_timeseries_T(expname, startyear, endyear, var, ndim, isub)
    # assembly and plot
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = gm.movave(data[var].values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, gt.cost(vv1, norm, idx_norm), color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[var].long_name)

    return pp


# gregory plot
def gregoryplot(expname, startyear, endyear, var_x, ndim_x, var_y, ndim_y, idx_ave, color):

    isub_x = False
    if '-' in var_x:
        isub_x = True

    isub_y = False
    if '-' in var_x:
        isub_y = True

    xdata = io.read_averaged_timeseries_T(expname, startyear, endyear, var_x, ndim_x, isub_x)
    ydata = io.read_averaged_timeseries_T(expname, startyear, endyear, var_y, ndim_y, isub_y)
    tt = xdata['time'].values.flatten()
    if idx_ave == 'ave':
        vx = xdata[var_x].values.flatten()
        vy = ydata[var_y].values.flatten()
        vx1 = vx; vy1 = vy; tt1 = tt
    elif idx_ave == 'mave':
        vx = gm.movave(xdata[var_x].values.flatten(),12)
        vy = gm.movave(ydata[var_y].values.flatten(),12)        
        vx1 = vx[6:-6]; vy1 = vy[6:-6]; tt1 = tt[6:-6]
    #colors = [tt1[i] for i in range(len(tt1))]
    pp = plt.plot(vx1, vy1, color) #, c=colors, cmap=plt.cm.coolwarm)        
    plt.xlabel(xdata[var_x].long_name)
    plt.ylabel(ydata[var_y].long_name)
    # cbar = plt.colorbar()
    # cbar.set_label(xdata['time'].long_name, ha='left', labelpad=10)

    return pp


def profile(expname, startyear, endyear, var, norm, idx_norm):

    data = io.read_averaged_profile_T(expname, startyear, endyear, var)
    zz = data['z'].values.flatten() 
    vv = data[var].values.flatten()
    pp = plt.plot(gt.cost(vv, norm, idx_norm),zz)
    plt.ylabel(data['z'].long_name)
    plt.xlabel(data[var].long_name)

    return pp

def hovmoller(expname, startyear, endyear, var, x_axis, y_axis, idx_norm):

    data = io.read_averaged_map_T(expname, startyear, endyear, var)
    # pp = plt.plot(x=x_axis, y=y_axis, c=var, cmap=plt.cm.coolwarm)
    #plt.xlabel(data['time'].long_name)
    #plt.ylabel(data['z'].long_name)
    #x = data[x_axis].values.flatten()
    #y = data[y_axis].values.flatten()
    #c = data[var].values.flatten().reshape(len(y),len(x))
    #pp = plt.pcolormesh(x, y, c)
    delta = (data[var] - data[var].isel(time=0))
    pp = delta.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.ylim(-5000,0)

    return pp


# add profiles, howmoller, pdf, monthly variability (JFMAMJJASOND) 
# fit over average trends, 2d maps of averaged quantities
# profiles of derivatives, check stability.

##########################################################################################
# two-field differences within the same temporal window

def timeseries_diff(exp1, exp2, startyear, endyear, var, ndim, norm, idx_norm, idx_ave, offset):

    isub = False
    if '-' in var:
        isub = True
        
    # read (or create) averaged data 
    data1 = io.read_averaged_timeseries_T(exp1, startyear, endyear, var, ndim, isub)
    data2 = io.read_averaged_timeseries_T(exp2, startyear, endyear, var, ndim, isub)
    # assembly and plot
    tt = data1['time'].values.flatten()
    delta = data2[var]-data1[var]
    if idx_ave == 'ave':
        vv = delta.values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = gm.movave(delta.values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2,gt.cost(vv1, norm, idx_norm))
    plt.xlabel(data1['time'].long_name)
    plt.ylabel(data1[var].long_name)

    return pp


def profiles_diff(exp1, exp2, startyear, endyear, var, norm, idx_norm):

    data1 = io.read_averaged_profile_T(exp1, startyear, endyear, var)
    data2 = io.read_averaged_profile_T(exp2, startyear, endyear, var)
    delta = data2[var]-data1[var]
    zz = data1['z'].values.flatten()     
    vv = delta.values.flatten()
    pp = plt.plot(gt.cost(vv, norm, idx_norm),zz)
    plt.xlabel(data1['z'].long_name)
    plt.ylabel(data1[var].long_name)

    return pp


##########################################################################################
# anomaly with respect to a meanfield

def timeseries_diff2(expname, startyear, endyear, refname, startref, endref, var, ndim, idx_norm, idx_ave, offset, color):

    isub = False
    if '-' in var:
        isub = True

    # read (or create) averaged data 
    data = io.read_averaged_timeseries_T(expname, startyear, endyear, var, ndim, isub)    
    mdata = io.read_averaged_field_T(refname, startref, endref, var, ndim)

    # assembly and plot
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        vm = gm.spacemean(expname, mdata[var], ndim)
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = gm.movave(data[var].values.flatten(),12)
        vm = gm.spacemean(expname, mdata[var], ndim)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, gt.cost(vv1, vm, idx_norm), color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel('Cost function')

    return pp


def timeseries_anomaly(expname, startyear, endyear, refname, startref, endref, var, ndim, idx_ave, offset, color):

    data = io.read_averaged_local_anomaly_T(expname, startyear, endyear, refname, startref, endref, var, ndim)
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = gm.movave(data[var].values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, vv1, color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[var].long_name)

    return pp

def hovmoller_anomaly(expname, startyear, endyear, refname, startref, endref, var):

    data = io.read_averaged_hovmoller_local_anomaly_T(expname, startyear, endyear, refname, startref, endref, var)    
    delta = data[var]#/data[var].isel(time=0)-1
    pp = delta.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.ylim(-5000,0)

    return pp