#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Regridding functions

Author: Alessandro Sozza (CNR-ISAC)
Date: Mar 2024
"""

import numpy as np
import xarray as xr

#################################################################################


def regrid_U_to_T(u, ndim):
    """
    Interpolate U component (zonal velocity) from U grid to T grid.
    U is staggered in the x direction relative to the T grid.
    
    """

    if ndim == '3D':
        u_coords = {'x': u['x'], 'y': u['y'], 'z': u['z']}
        u_on_t_grid = u.interp(x=u_coords['x'] + 0.5, y=u_coords['y'], z=u_coords['z'])
    elif ndim == '2D':
        u_coords = {'x': u['x'], 'y': u['y']}
        u_on_t_grid = u.interp(x=u_coords['x'] + 0.5, y=u_coords['y'])
    else:
        raise ValueError(" Invalid dimensions ")

    return u_on_t_grid

def regrid_V_to_T(v, ndim):
    """
    Interpolate V component (meridional velocity) from V grid to T grid.
    V is staggered in the y direction relative to the T grid.
    
    """
    
    if ndim == '3D':
        v_coords = {'x': v['x'], 'y': v['y'], 'z': v['z']}
        v_on_t_grid = v.interp(x=v_coords['x'] + 0.5, y=v_coords['y'], z=v_coords['z'])
    elif ndim == '2D':
        v_coords = {'x': v['x'], 'y': v['y']}
        v_on_t_grid = v.interp(x=v_coords['x'] + 0.5, y=v_coords['y'])
    else:
        raise ValueError(" Invalid dimensions ")

    return v_on_t_grid

def regrid_W_to_T(w, ndim):
    """
    Interpolate W component (vertical velocity) from W grid to T grid.
    W is staggered in the z direction relative to the T grid.

    """

    if ndim == '3D':
        w_coords = {'x': w['x'], 'y': w['y'], 'z': w['z']}
        w_on_t_grid = w.interp(x=w_coords['x'] + 0.5, y=w_coords['y'], z=w_coords['z'])
    elif ndim == '2D':
        w_coords = {'x': w['x'], 'y': w['y']}
        w_on_t_grid = v.interp(x=w_coords['x'] + 0.5, y=w_coords['y'])
    else:
        raise ValueError(" Invalid dimensions ")

    return w_on_t_grid

#################################################################################
