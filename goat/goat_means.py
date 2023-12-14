#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GOAT library for mathematical operations 
(averaging, transformations etc...)

Authors
Alessandro Sozza (CNR-ISAC, Dec 2023)
"""

import os
import numpy as np
import xarray as xr
from sklearn.linear_model import LinearRegression
import goat_tools as gt
import goat_io as io


def elements(expname):

    df = {}
    domain = io.read_domain(expname=expname)
    df['vol'] = domain['e1t']*domain['e2t']*domain['e3t_0']
    df['area'] = domain['e1t']*domain['e2t']
    df['dx'] = domain['e1t']
    df['dy'] = domain['e2t']
    df['dz'] = domain['e3t_0']

    return df

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

def movave(ydata, N):

    #y_list = np.array(ydata.values.flatten())
    y_padded = np.pad(ydata, (N//2, N-1-N//2), mode='edge')
    y_smooth = np.convolve(y_padded, np.ones((N,))/N, mode='valid')

    return y_smooth

def runave(ydata):
    
    ym = [0] * len(ydata)
    for i in range(len(ydata)):
        if (i==0):
            ym[i] = ydata[i]
        else:
            ym[i] = ym[i-1]+(ydata[i]-ym[i-1])/i

    return ym

def ave_T(expname, year, var):

    df = elements(expname=expname)   
    data = io.read_T(expname=expname, year=year)
    ave = data[var].weighted(df['vol']).mean(dim=['time', 'z', 'y', 'x']).values

    return ave

def ave_T_sub(expname, year, var, z1, z2):

    df = elements(expname=expname)
    subvol = df['vol'].isel(z=slice(z1,z2))
    data = io.read_T(expname=expname, year=year)
    subvar = data[var].isel(z=slice(z1,z2))
    ave = subvar.weighted(subvol).mean(dim=['time', 'z', 'y', 'x']).values

    return ave
