#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Checks

Authors
Alessandro Sozza (CNR-ISAC, Mar 2024)
"""

import subprocess
import numpy as np
import os
import glob
import shutil
import yaml
import random
import xarray as xr
import dask
import cftime
import nc_time_axis
import matplotlib.pyplot as plt


def check_fit(expname, leg, yearspan, yearleap):
    """ Function to forecast local temperature using linear fit """

    i=random.randint(0, to_wonan.shape[1]-1)
    kji = osm.flatten_to_triad(i, 31, 148, 180)
    model = LinearRegression()
    x_row = np.array(x).reshape(len(x),-1)
    y_row = to_wonan[:,i].reshape(len(x),-1)
    model.fit(x_row, y_row)
    mp = model.coef_[0][0]
    qp = model.intercept_[0]
    yf = model.predict([[xf]])
    ym = osm.movave(y_row.flatten(),12).reshape(len(x),-1)
    yp = []; xp = []
    for i in range(len(x)*2):
        xp.append(startyear+i/12.)
        yp.append(mp*(startyear+i/12.)+qp)
    pp =plt.plot(x_row,y_row)
    pp = plt.plot(x,ym)
    pp = plt.plot(xp,yp)
    pp = plt.scatter(xf,yf, color='green')
    plt.ylabel('temperature')
    plt.xlabel('time')
    plt.title('')
    plt.title(' (k,j,i) = {}'.format(kji))
    plt.gca().legend(('local trend','moving average','fit','projected value'))

    return pp 


def check_EOF(expname, var, leg, yearspan, yearleap):
    """ Function to forecast temperature field using EOF """

    dirs = io.folders(expname)

    # create EOF timeseries with CDO

    # read pattern and do the forecast
    pattern = xr.open_mfdataset(os.path.join(dirs['eof'], 'pattern.nc'), use_cftime=True, preprocess=io.preproc_pattern)
    variance = xr.open_mfdataset(os.path.join(dirs['eof'], 'variance.nc'), use_cftime=True, preprocess=io.preproc_variance)
    scalar = pattern.isel(time=0)*0
    for k in range(10):
        filename = os.path.join(mainpath, f"timeseries0000{k}.nc")
        timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=io.preproc_timeseries)
        p = timeseries.polyfit(dim='time', deg=1, skipna = True)
        fit = xr.polyval(data['time'], p.tos_polyfit_coefficients)
        yf = xr.polyval(xf, p.tos_polyfit_coefficients)
        step = pattern.isel(time=k)
        scalar = scalar + yf.values.flatten()*step

    # plot

    return pp 