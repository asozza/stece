#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Regridding functions

Author: Alessandro Sozza (CNR-ISAC)
Date: Mar 2024
"""

import numpy as np
import xarray as xr

from osprey.actions.domain import read_domain


#################################################################################
#
#    W   V --- F 
#     \  |     |
#      \ |     |
#        T --- U
#

def regrid_U_to_T(u, ndim):
    """
    Interpolate U component (zonal velocity) from U grid to T grid.
    U is staggered in the x direction relative to the T grid.
    
    """

    domain = read_domain('ORCA2') 

    if ndim == '3D':
        u_coords = {'x': u['x'], 'y': u['y'], 'z': domain['z']}
        u_on_t_grid = u.interp(x=u_coords['x'] - 0.5, y=u_coords['y'], z=u_coords['z'])
    elif ndim == '2D':
        u_coords = {'x': u['x'], 'y': u['y']}
        u_on_t_grid = u.interp(x=u_coords['x'] - 0.5, y=u_coords['y'])
    else:
        raise ValueError(" Invalid dimensions ")

    return u_on_t_grid

def regrid_V_to_T(v, ndim):
    """
    Interpolate V component (meridional velocity) from V grid to T grid.
    V is staggered in the y direction relative to the T grid.
    
    """

    domain = read_domain('ORCA2')    

    if ndim == '3D':       
        v_coords = {'x': v['x'], 'y': v['y'], 'z': domain['z']}
        v_on_t_grid = v.interp(x=v_coords['x'], y=v_coords['y'] - 0.5, z=v_coords['z'])
    elif ndim == '2D':
        v_coords = {'x': v['x'], 'y': v['y']}
        v_on_t_grid = v.interp(x=v_coords['x'], y=v_coords['y'] - 0.5)
    else:
        raise ValueError(" Invalid dimensions ")

    return v_on_t_grid

def regrid_W_to_T(w, ndim):
    """
    Interpolate W component (vertical velocity) from W grid to T grid.
    W is staggered in the z direction relative to the T grid.

    """

    domain = read_domain('ORCA2')

    if ndim == '3D':
        w_on_t_grid = w.interp(z=domain['nav_lev'].drop_vars('time'))
    elif ndim == '2D':
        w_on_t_grid = w
    else:
        raise ValueError(" Invalid dimensions ")

    return w_on_t_grid

#################################################################################
