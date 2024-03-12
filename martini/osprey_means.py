#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 _____  __________  ____  ______   __ 
/  __ \/   __   _ \|  _ \|  ___ \ / / 
| |  |    |_ | |_|   |_|   |__ \ V /  
| |  | |\_  \|  __/|    /|  __| | |   
| |__| |__|    |   | |\ \| |____| |   
\___________/|_|   |_| \__________|   

OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Osprey library for mathematical operations

Authors
Alessandro Sozza (CNR-ISAC, Mar 2024)
"""

import os
import numpy as np
import xarray as xr
import cftime
import datetime
import time
from sklearn.linear_model import LinearRegression
import osprey_io as io


def epoch(date):

    s = time.mktime(date.timetuple())

    return s

def yearFraction(date):

    StartOfYear = datetime.datetime(date.year,1,1,0,0,0)
    EndOfYear = datetime.datetime(date.year+1,1,1,0,0,0)
    yearElapsed = epoch(date)-epoch(StartOfYear)
    yearDuration = epoch(EndOfYear)-epoch(StartOfYear)
    Frac = yearElapsed/yearDuration

    return  date.year + Frac

def dateDecimal(date):

    x1 = [yearFraction(t) for t in date]

    return x1

# container for multiple cost functions
def cost(var, varref, idx):

    # normalized
    if idx == 'norm':
        x = var/varref
    # difference (with sign)
    if idx == 'diff':
        x = (var-varref)
    # relative difference
    if idx == 'rdiff':
        x = (var-varref)/varref    
    # absolute error
    if idx == 'abs':
        x = abs(var-varref)
    # relative error
    if idx == 'rel':
        x = abs(var-varref)/varref
    # variance
    if idx == 'var':
        x = pow(var-varref,2)
    # normalized/relative variance
    if idx == 'rvar':
        x = pow(var-varref,2)/pow(varref,2)
    # other cost functions: exp? or atan?

    return x

# define differential forms for integrals
def elements(expname):

    df = {}
    domain = io.read_domain(expname=expname)
    df['vol'] = domain['e1t']*domain['e2t']*domain['e3t_0']
    df['area'] = domain['e1t']*domain['e2t']
    df['dx'] = domain['e1t']
    df['dy'] = domain['e2t']
    df['dz'] = domain['e3t_0']

    return df

# interpolated moving average
def intave(xdata, ydata, N):

    x_orig = np.array(gt.dateDecimal(xdata.values))

    for i in range(N):    
        x_filled = np.array(gt.dateDecimal(xdata.where(xdata['time.month']==i+1,drop=True).values))
        y_filled = np.array(ydata.where(xdata['time.month']==i+1,drop=True).values.flatten())
        if (i==0):
            y_smooth = np.interp(x_orig, x_filled, y_filled)/N
        else:
            y_smooth += np.interp(x_orig, x_filled, y_filled)/N
    
    return y_smooth

# moving/running average
def movave(ydata, N):

    #y_list = np.array(ydata.values.flatten())
    y_padded = np.pad(ydata, (N//2, N-1-N//2), mode='edge')
    y_smooth = np.convolve(y_padded, np.ones((N,))/N, mode='valid')

    return y_smooth

# cumulative average
def cumave(ydata):
        
    ave = np.cumsum(ydata)
    for i in range(1,len(ydata)):
        ave[i] = ave[i]/(i+1)

    return ave

# global average over space and time
def ave_T(expname, year, var):

    df = elements(expname=expname)   
    data = io.read_T(expname=expname, year=year)
    ave = data[var].weighted(df['vol']).mean(dim=['time', 'z', 'y', 'x']).values

    return ave

# global average in a vertical slab
def ave_T_sub(expname, year, var, z1, z2):

    df = elements(expname=expname)
    subvol = df['vol'].isel(z=slice(z1,z2))
    data = io.read_T(expname=expname, year=year)
    subvar = data[var].isel(z=slice(z1,z2))
    ave = subvar.weighted(subvol).mean(dim=['time', 'z', 'y', 'x']).values

    return ave

# global average in a time window
def ave_T_window(expname, startyear, endyear, var):

    df = elements(expname=expname)   
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    ave = data[var].weighted(df['vol']).mean(dim=['time', 'z', 'y', 'x']).values

    return ave

# mean state
def mean_state(expname, startyear, endyear):

    df = elements(expname=expname)
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    field = data.mean(dim=['time'])

    return field

def anomaly_local(expname, year, field, idx):
    
    data = io.read_T(expname=expname, year=year)
    delta = cost(data, field, idx)

    return delta