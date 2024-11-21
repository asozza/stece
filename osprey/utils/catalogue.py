#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EC-Earth catalogue
Dictionaries of variables, coordinates and diagnostics' features

Author: Alessandro Sozza (CNR-ISAC)
Date: July 2024
"""

import gsw  # Gibbs SeaWater library for oceanographic calculations
from osprey.means.regrid import regrid_U_to_T, regrid_V_to_T, regrid_W_to_T 

def _density(thetao, so):
    """ Potential density """

    pressure = gsw.p_from_z(-thetao['z'], thetao['lat'])
    rho = gsw.density.rho(so, thetao, pressure)

    return rho


def observables(component):
    """ Dictionary of EC-Earth variables """

    if component == 'nemo':
        varlist = {
            # T grid
            'e3t': {'dim': '3D', 
                    'grid': 'T',
                    'units': 'm', 
                    'long_name': 'T-cell thickness'},
            'thetao' : {'dim': '3D', 
                        'grid': 'T',
                        'units': 'degC', 
                        'long_name': 'Temperature'},
            'so': {'dim': '3D', 
                   'grid': 'T',
                   'units': 'PSU', 
                   'long_name': 'Salinity'},
            'tos': {'dim': '2D', 
                    'grid': 'T',
                    'units': 'degC', 
                    'long_name': 'Sea-surface temperature'},
            'sos': {'dim': '2D', 
                    'grid': 'T',
                    'units': 'PSU', 
                    'long_name': 'Sea-surface salinity'},
            'zos': {'dim': '2D', 
                    'grid': 'T',
                    'units': 'm', 
                    'long_name': 'Sea surface height'},
            'sstdcy': {'dim': '2D', 
                       'grid': 'T',
                       'units': 'degC', 
                       'long_name': 'Sea-surface temperature diurnal cycle'},
            'mldkz5': {'dim': '2D', 
                       'grid': 'T',
                       'units': 'm', 
                       'long_name': 'Turbocline depth'}, # (Kz=5e-4)
            'mldr10_1': {'dim': '2D', 
                         'grid': 'T',
                         'units': 'm', 
                         'long_name': 'Mixed layer depth'}, # (dsigma=0.01 wrt 10m)
            'mldr10_1dcy': {'dim': '2D', 
                            'grid': 'T',
                            'units': 'm', 
                            'long_name': 'Amplitude of mldr10_1 diurnal cycle'},
            'sbt': {'dim': '2D', 
                    'grid': 'T',
                    'units': 'degC', 
                    'long_name': 'Sea bottom temperature'},
            'heatc': {'dim': '2D', 
                      'grid': 'T',
                      'units': 'J/m^2', 
                      'long_name': 'Heat content vertically integrated'},
            'saltc': {'dim': '2D', 
                      'grid': 'T',
                      'units': 'PSU*kg/m^2', 
                      'long_name': 'Salt content vertically integrated'},
            'wfo': {'dim': '2D', 
                    'grid': 'T',
                    'units': 'kg/m^2/s', 
                    'long_name': 'Net upward water flux'},
            'qsr_oce': {'dim': '2D', 
                        'grid': 'T',
                        'units': 'W/m^2', 
                        'long_name': 'Solar heat flux at ocean surface'},
            'qns_oce': {'dim': '2D', 
                        'grid': 'T',
                        'units': 'W/m^2', 
                        'long_name': 'Non-solar heat flux at ocean surface (including E-P)'},
            'qt_oce': {'dim': '2D', 
                       'grid': 'T',
                       'units': 'W/m^2', 
                       'long_name': 'Total flux at ocean surface'},
            'sfx': {'dim': '2D', 
                    'grid': 'T',
                    'units': 'g/m2/s', 
                    'long_name': 'Downward salt flux'},
            'taum': {'dim': '2D', 
                     'grid': 'T',
                     'units': 'N/m^2', 
                     'long_name': 'Surface downward wind stress'},
            'windsp': {'dim': '2D', 
                       'grid': 'T',
                       'units': 'm/s', 
                       'long_name': 'Wind speed'},
            'precip': {'dim': '2D', 
                       'grid': 'T',
                       'units': 'kg/m2/s', 
                       'long_name': 'Precipitation flux'},
            'snowpre': {'dim': '2D', 
                        'grid': 'T',
                        'units': 'kg/m2/s', 
                        'long_name': 'Snowfall flux'},

            # U-grid
            'e3u': {'dim': '3D', 
                    'grid': 'U',
                    'units': 'm', 
                    'long_name': 'U-cell thickness'},
            'uo': {'dim': '3D', 
                   'grid': 'U',                   
                   'units': 'm/s', 
                   'long_name': 'Ocean current along i-axis'},
            'uos': {'dim': '2D', 
                    'grid': 'U',
                    'units': 'm/s', 
                    'long_name': 'Ocean surface current along i-axis'},
            'tauuo': {'dim': '2D', 
                      'grid': 'U',
                      'units': 'N/m^2', 
                      'long_name': 'Wind stress along i-axis'},
            'uocetr_eff': {'dim': '3D', 
                           'grid': 'U',
                           'units': 'm^3/s', 
                           'long_name': 'Effective ocean transport along i-axis'},
            'vozomatr': {'dim': '3D', 
                         'grid': 'U',
                         'units': 'kg/s', 
                         'long_name': 'Ocean mass transport along i-axis'},
            'sozohetr': {'dim': '2D', 
                         'grid': 'U',
                         'units': 'W', 
                         'long_name': 'Heat transport along i-axis'},
            'sozosatr': {'dim': '2D', 
                         'grid': 'U',
                         'units': '1e-3*kg/s', 
                         'long_name': 'Salt transport along i-axis'},

            # V-grid
            'e3v': {'dim': '3D', 
                    'grid': 'V',
                    'units': 'm', 
                    'long_name': 'V-cell thickness'},
            'vo': {'dim': '3D', 
                   'grid': 'V',
                   'units': 'm/s', 
                   'long_name': 'Ocean current along j-axis'},
            'vos': {'dim': '2D',
                    'grid': 'V', 
                    'units': 'm/s', 
                    'long_name': 'Ocean surface current along j-axis'},
            'tauvo': {'dim': '2D',
                      'grid': 'V', 
                      'units': 'N/m^2', 
                      'long_name': 'Wind stress along j-axis'},
            'vocetr_eff': {'dim': '3D',
                           'grid': 'V', 
                           'units': 'm^3/s', 
                           'long_name': 'Effective ocean transport along j-axis'},
            'vomematr': {'dim': '3D', 
                         'grid': 'V',
                         'units': 'kg/s', 
                         'long_name': 'Ocean mass transport along j-axis'},
            'somehetr': {'dim': '2D', 
                         'grid': 'V',
                         'units': 'W', 
                         'long_name': 'Heat transport along j-axis'},
            'somesatr': {'dim': '2D', 
                         'grid': 'V',
                         'units': '1e-3*kg/s', 
                         'long_name': 'Salt transport along j-axis'},

            # W-grid
            'e3w': {'dim': '3D', 
                    'grid': 'W',
                    'units': 'm', 
                    'long_name': 'W-cell thickness'},
            'wo': {'dim': '3D', 
                   'grid': 'W',
                   'units': 'm/s', 
                   'long_name': 'Ocean vertical velocity'},
            'difvho': {'dim': '3D',
                       'grid': 'W', 
                       'units': 'm^2/s', 
                       'long_name': 'Vertical eddy diffusivity'},         
            'vovematr': {'dim': '3D', 
                         'grid': 'W',
                         'units': 'kg/s', 
                         'long_name': 'Vertical mass transport'},
            'av_wave': {'dim': '3D', 
                        'grid': 'W',
                        'units': 'm^2/s', 
                        'long_name': 'Internal wave-induced vertical diffusivity'},
            'bn2': {'dim': '3D',
                    'grid': 'W', 
                    'units': '1/s^2', 
                    'long_name': 'Squared Brunt-Vaisala frequency'},
            'bflx_iwm': {'dim': '3D',
                         'grid': 'W', 
                         'units': 'W/kg', 
                         'long_name': 'Internal wave-induced buoyancy flux'},
            'pcmap_iwm': {'dim': '2D', 
                          'grid': 'W', 
                          'units': 'W/m^2', 
                          'long_name': 'Power consumption by wave-driven mixing'},
            'emix_iwm': {'dim': '3D', 
                         'grid': 'W',
                         'units': 'W/kg', 
                         'long_name': 'Power density available for mixing'},
            'av_ratio': {'dim': '3D', 
                         'grid': 'W',
                         'units': '-', 
                         'long_name': 'S over T diffusivity ratio'},

            # ice

            # derived quantities
            'keos': {'dim': '2D', 
                     'grid': ['U', 'V'], 
                     'units': 'm^2/s^2', 
                     'long_name': 'Surface Kinetic Energy', 
                     'dependencies': ['uos', 'vos'],
                     'operation': lambda uos, vos: 0.5 * (uos**2 + vos**2),
                     'preprocessing': {
                         'uos': lambda data: regrid_U_to_T(u=data, ndim='2D'),
                         'vos': lambda data: regrid_V_to_T(v=data, ndim='2D')}},                       
            'keoh': {'dim': '3D', 
                     'grid': ['U', 'V'], 
                     'units': 'm^2/s^2', 
                     'long_name': 'Horizontal Kinetic Energy', 
                     'dependencies': ['uo', 'vo'],
                     'operation': lambda uo, vo: 0.5 * (uo**2 + vo**2),
                     'preprocessing': {
                         'uo': lambda data: regrid_U_to_T(u=data, ndim='3D'),
                         'vo': lambda data: regrid_V_to_T(v=data, ndim='3D')}},  
            'keo': {'dim': '3D', 
                    'grid': ['U', 'V', 'W'], 
                    'units': 'm^2/s^2', 
                    'long_name': 'Total Kinetic Energy', 
                    'dependencies': ['uo', 'vo', 'wo'],
                    'operation': lambda uo, vo, wo: 0.5 * (uo**2 + vo**2 + wo**2),
                    'preprocessing': {
                        'uo': lambda data: regrid_U_to_T(u=data, ndim='3D'),
                        'vo': lambda data: regrid_V_to_T(v=data, ndim='3D'),
                        'wo': lambda data: regrid_W_to_T(w=data, ndim='3D')}},
            'rho': {'dim': '3D', 
                    'grid': ['T', 'T'], 
                    'units': 'kg/m^3', 
                    'long_name': 'Potential Density', 
                    'dependencies': ['thetao', 'so'],
                    'operation': lambda thetao, so: _density(thetao, so)},
            'woto': {'dim': '3D', 
                     'grid': ['T', 'W'], 
                     'units': 'K*m/s', 
                     'long_name': 'Buoyancy flux', 
                     'dependencies': ['thetao', 'wo'],
                     'operation': lambda thetao, wo: thetao*wo}
        }

    elif component == 'oifs':
        varlist = {
            'tas': {'dim': '2D',
                    'units': 'K',
                    'long_name': 'Near-Surface Air Temperature'}
        }

    else:
        raise ValueError(f"Unknown component: {component}. Valid components are nemo and oifs.")

    return varlist


def coordinates(use_cft):
    """ Dictionary of coordinates in EC-Earth """

    coordlist = {
        
        "time": {"axis": "T", 
                 "standard_name": "time", 
                 "long_name": "time", 
                 "calendar": "gregorian", 
                 "units": "seconds since 1990-01-01 00:00:00" if use_cft else "years since 1990.00", 
                 "origin": "1990-01-01 00:00:00" if use_cft else "1990.00"},
        "month": {"standard_name": "month",
                 "long_name": "month",                 
                 "units": "months"},
        "season": {"standard_name": "season",
                 "long_name": "season",                 
                 "units": "seasons"},
        "year": {"standard_name": "year",
                 "long_name": "year",                 
                 "units": "years",
                 "origin": "1990"},
        "lat": {"standard_name": "latitude",
                "long_name": "latitude",
                "units": "deg"},
        "lon": {"standard_name": "longitude",
                "long_name": "longitude",
                "units": "deg"},
        "z": {"standard_name": "depth",
              "long_name": "depth",
              "units": "m",
              "positive": "up"}

    }

    return coordlist


# Dictionary of abbreviations for diagnostics, format and metric
def abbrevations(entry_type):
    """ Dictionary of abbreviations for diagnostics, format and metric """

    if entry_type == 'diagname':
        options = {
            'scalar': 'scalar',
            'timeseries': 'series',
            'profile': 'prof',
            'hovmoller': 'hovm',
            'map': 'map',
            'field': 'fld',
            'pdf': 'pdf'
        }

    elif entry_type == 'format': 
        options = {
            'plain': 'p',
            'global': 'g',
            'yearly': 'y',
            'monthly': 'm',
            'seasonally': 's'
        }
            
    elif entry_type == 'metric': 
        options = {
            'base': 'B',
            'diff': 'D',
            'var': 'V',
            'rel': 'R'
    }
        
    elif entry_type == 'use_cft':
        options = {
            True: 'cft',
            False: 'dyt'
        }        

    else:
        raise ValueError(f"Unknown entry: {entry_type}. Valid entries are diagname, format, metric and use_cft.")

    return options