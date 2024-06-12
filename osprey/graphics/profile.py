#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for profiles

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


def profile(expname, startyear, endyear, var, norm, idx_norm):
    """ graphics profile """

    data = osi.read_averaged_profile_T(expname, startyear, endyear, var)
    zz = data['z'].values.flatten() 
    vv = data[var].values.flatten()
    pp = plt.plot(osm.cost(vv, norm, idx_norm),zz)
    plt.ylabel(data['z'].long_name)
    plt.xlabel(data[var].long_name)

    return pp


def profile_diff(exp1, exp2, startyear, endyear, var, norm, idx_norm):
    """ graphics of profile difference """

    data1 = osi.read_averaged_profile_T(exp1, startyear, endyear, var)
    data2 = osi.read_averaged_profile_T(exp2, startyear, endyear, var)
    delta = data2[var]-data1[var]
    zz = data1['z'].values.flatten()     
    vv = delta.values.flatten()
    pp = plt.plot(osm.cost(vv, norm, idx_norm),zz)
    plt.xlabel(data1['z'].long_name)
    plt.ylabel(data1[var].long_name)

    return pp

