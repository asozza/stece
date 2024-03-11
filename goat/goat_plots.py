#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
  ____   ____     _   _____
 / __/  / __ \   / \ |_   _|
| |  _ | |  | | / _ \  | |  
| |_| || |__| |/ /_\ \ | |  
 \____| \____//_/   \_\|_|  

GOAT: Global Ocean Analysis and Trends
------------------------------------------------------
GOAT library for plots

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import os
import numpy as np
import xarray as xr
import cftime
import matplotlib.pyplot as plt
import goat_tools as gt
import goat_io as io
import goat_means as gm

# standard time series
def plot_ts_ave3d(expname, startyear, endyear, var, norm, idx):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten()
    if idx == 'norm':
        pp = plt.plot(tt,vv/norm) # rescaled
    if idx == 'abs':
        pp = plt.plot(tt,vv-norm) # anomaly
    if idx == 'rel': 
        pp = plt.plot(tt,vv/norm-1) # normalized anomaly
    if idx == 'var':
        pp = plt.plot(tt,(vv-norm)*(vv-norm)) # squared error / variance
    if idx == 'rvar':
        pp = plt.plot(tt,(vv-norm)*(vv-norm)/(norm*norm)) # normalized variance

    return pp


# time series with moving average
def plot_ts_ma3d(expname, startyear, endyear, var, norm, idx):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    tt1 = tt[6:-6]; vv1 = vv[6:-6]
    pp = plt.plot(tt1,gt.cost(vv1, norm, idx))

    return pp

def plot_ts_ma2d(expname, startyear, endyear, var, norm, idx):

    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['area']).mean(dim=['y', 'x']).values.flatten(),12)
    tt1 = tt[6:-6]; vv1 = vv[6:-6]
    pp = plt.plot(tt1,gt.cost(vv1, norm, idx))

    return pp

# time derivative
def plot_ts_ma3d_dt(expname, startyear, endyear, var, norm, idx):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    dd = np.diff(vv)
    tt1 = tt[6:-7]; dd1 = dd[6:-6]
    pp = plt.plot(tt1,gt.cost(dd1, norm, idx))

    return pp

# local time derivative
def plot_ts_ma3d_dt2(expname, startyear, endyear, var, norm, idx):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    dvar = data[var].diff("time", 1)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(dvar.weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    tt1 = tt[6:-7]; vv1 = vv[6:-6]
    pp = plt.plot(tt1,gt.cost(vv1, norm, idx))

    return pp

# average on a sub-domain
def plot_ts_ma3d_sub(expname, startyear, endyear, var, z1, z2, norm, idx):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    subvol = df['vol'].isel(z=slice(z1,z2))
    subvar = data[var].isel(z=slice(z1,z2))
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(subvar.weighted(subvol).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    tt1 = tt[6:-6]; vv1 = vv[6:-6]
    pp = plt.plot(tt1,gt.cost(vv1, norm, idx))

    return pp

# running average
def plot_ts_ra3d(expname, startyear, endyear, var):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    vv1 = vv[6:-6]
    rr = gm.cumave(vv1)
    pp = plt.plot(tt[6:-6],rr)

    return pp

def plot_ts_ra2d(expname, startyear, endyear, var):

    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['area']).mean(dim=['y', 'x']).values.flatten(),12)
    vv1 = vv[6:-6]
    rr = gm.cumave(vv1)
    pp = plt.plot(tt[6:-6],rr)

    return pp

## gregory plots
def gregory_plot_ma3d(expname, startyear, endyear, var1, var2):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tf = len(data['time'].values) 
    vv1 = gm.movave(data[var1].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    vv2 = gm.movave(data[var2].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    pp = plt.plot(vv1[6:-6],vv2[6:-6])

    return pp


# moving average in a specific spot
def plot_ts_ma3d_xyz(expname, startyear, endyear, var, x0, y0, z0, norm, idx):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].isel(x=x0,y=y0,z=z0).values.flatten(),12)
    if idx == 'norm':
        pp = plt.plot(tt[6:-6],vv[6:-6]/norm) # rescaled
    if idx == 'abs':
        pp = plt.plot(tt[6:-6],vv[6:-6]-norm) # anomaly
    if idx == 'rel': 
        pp = plt.plot(tt[6:-6],vv[6:-6]/norm-1) # normalized anomaly

    return pp

def plot_ts_ma3d_xyz_dt(expname, startyear, endyear, var, x0, y0, z0, norm, idx):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    dd = np.diff(vv)
    if idx == 'norm':
        pp = plt.plot(tt[6:-7],dd[6:-6]/norm) # rescaled
    if idx == 'abs':
        pp = plt.plot(tt[6:-7],dd[6:-6]-norm) # anomaly
    if idx == 'rel': 
        pp = plt.plot(tt[6:-7],dd[6:-6]/norm-1) # normalized anomaly

    return pp


# profiles
def plot_prof(expname, startyear, endyear, var):

    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    zz = data['z'].values.flatten()
    vv = data[var].weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()
    pp = plt.plot(vv,zz)

    return pp

def plot_prof_dz(expname, startyear, endyear, var):

    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    dvar = data['to'].diff("z", 1)
    df = gm.elements(expname=expname)
    zz = data['z'].values.flatten()
    vv = dvar.weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()
    pp = plt.plot(vv,zz)

    return pp

def prof_anomaly(expname, startyear, endyear, var):

    data1 = io.read_T(expname=expname, year=startyear)
    data2 = io.read_T(expname=expname, year=endyear)
    df = gm.elements(expname=expname)
    zz = data1['z'].values.flatten()
    vv1 = data1[var].weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()
    vv2 = data2[var].weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()
    pp = plt.plot(pow(vv2-vv1,2)/pow(vv2,2),zz)

    return pp


# maps and density plots
def map2d(expname, year, month, var, Tmin, Tmax):

    data = io.read_T(expname=expname, year=year)
    if Tmin == Tmax:
        pp = data[var].isel(time=month-1).plot()
    else:
        pp = data[var].isel(time=month-1).plot(vmin=Tmin, vmax=Tmax)
    
    return pp

def map2d_anomaly(expname, year1, year2, month, var, Tmin, Tmax):

    data1 = io.read_T(expname=expname, year=year1)
    data2 = io.read_T(expname=expname, year=year2)    
    delta = xr.where(data2[var]!=0, pow(data2[var].values-data1[var].values,2), 0.0)
    if Tmin == Tmax:
        pp = delta.isel(time=month-1).plot()
    else:
        pp = delta.isel(time=month-1).plot(vmin=Tmin, vmax=Tmax)
    
    return pp

def hist2d_anomaly(expname, year1, year2, month, var):

    data1 = io.read_T(expname=expname, year=year1)
    data2 = io.read_T(expname=expname, year=year2)    
    delta = xr.where(data2[var]!=0, pow(data2[var].values-data1[var].values,2)/pow(data2[var].values,2), 0.0)
    # pp = plt.hist(delta.isel(time=month-1).values.flatten)
    
    return delta

def hist2d_var(expname, year1, year2, month, var):

    data1 = io.read_T(expname=expname, year=year1)
    data2 = io.read_T(expname=expname, year=year2)    
    delta = xr.where(data2[var]!=0, pow(data2[var].values-data1[var].values,2), 0.0)
    # pp = plt.hist(delta.isel(time=month-1).values.flatten)
    
    return delta

def map3d_anomaly(expname, year1, year2, month, var, Tmin, Tmax):

    data1 = io.read_T(expname=expname, year=year1)
    data2 = io.read_T(expname=expname, year=year2)    
    delta = xr.where(data2[var]!=0, pow(data1[var].values-data2[var].values,2), 0.0)
    df = gm.elements(expname=expname)
    meandelta = delta.isel(time=month-1).weighted(df['dz']).mean(dim=['z'])
    if Tmin == Tmax:
        pp = meandelta.plot()
    else:
        pp = meandelta.plot(vmin=Tmin, vmax=Tmax)
    
    return pp

def plot_hovmoller(expname, startyear, endyear, var, z1, z2, cmin, cmax):

    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    data[var] = xr.where(data[var]!=0, data[var]/data[var].isel(time=0)-1.0,0.0) 
    hovm = data[var].weighted(df['area']).mean(dim=['y', 'x'])    
    if cmin == cmax:
        pp = hovm.plot(y='z', ylim=(-z2, -z1))
    else:
        pp = hovm.plot(y='z', ylim=(-z2, -z1), vmin=cmin, vmax=cmax)
        plt.yscale('log')

    return pp

def map_mean_anomaly(expname, year, startyear, endyear, var, idx):

    df = gm.elements(expname)
    meanfield = gm.mean_state(expname, startyear, endyear)    
    field = gm.anomaly_local(expname, year, meanfield, idx)
    field = field.rename_vars({'to': 'Temperature Anomaly'})
    pp = field['Temperature Anomaly'].weighted(df['dz']).mean(dim=['z','time']).plot()

    return pp

def timeseries_mean_anomalies(expname, year1, year2, startyear, endyear, var, idx):

    ave = gm.ave_T_window(expname, startyear, endyear, var)
    data = io.readmf_T(expname, year1, year2)
    df = gm.elements(expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    tt1 = tt[6:-6]
    vv1 = vv[6:-6]
    pp = plt.plot(tt1,gt.cost(vv1, ave, idx))

    return pp

def timeseries_anomaly_set(expname, year1, year2, startyear, endyear, var):
    
    indices = ['abs','rel','var','rvar'] # diff, rdiff
    ave = gm.ave_T_window(expname, startyear, endyear, var)
    data = io.readmf_T(expname, year1, year2)
    df = gm.elements(expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    tt1 = tt[6:-6]; vv1 = vv[6:-6]
    for idx in indices:
        pp = plt.plot(tt1,gt.cost(vv1, ave, idx))
    plt.gca().legend(('abs','rel','var','rvar'))

    return pp
