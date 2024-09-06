#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Variable dictionary per component

Author: Alessandro Sozza (CNR-ISAC)
Date: July 2024
"""

def vardict(component):
    """ Dictionary of EC-Earth variables """

    if component == 'nemo':
        list = {
            # T grid
            'e3t': '3D', # T-cell thickness
            'thetao' : '3D', # temperature
            'so': '3D', # salinity
            'tos': '2D', # sea-surface temperature
            'sos': '2D', # sea-surface salinity
            'zos': '2D', # sea-surface height
            'sstdcy': '2D', # sea-surface temperature diurnal cycle
            'mldkz5': '2D', # turbocline depth (Kz=5e-4)
            'mldr10_1': '2D', # mixed layer depth (dsigma=0.01 wrt 10m)
            'mldr10_1dcy': '2D', # amplitude of mldr10_1 diurnal cycle
            'sbt': '2D', # sea bottom temperature
            'heatc': '2D', # heat content
            'saltc': '2D', # salt content
            'wfo': '2D', # net upward water flux
            'qsr_oce': '2D', # solar heat flux at ocean surface
            'qns_oce': '2D', # non-solar heat flux at ocean surface (including E-P)
            'qt_oce': '2D', # total flux at ocean surface
            'sfx': '2D', # downward salt flux
            'taum': '2D', # surface downward wind stress
            'windsp': '2D', # wind speed
            'precip': '2D', # precipitation flux
            'snowpre': '2D', # snowfall flux
            # U-grid
            'e3u': '3D', # U-cell thickness
            'uo': '3D', # ocean current along i-axis
            'uos': '2D', # ocean surface current along i-axis
            'tauuo': '2D', # wind stress along i-axis
            'uocetr_eff': '3D', # effective ocean volume transport along i-axis
            'vozomatr': '3D', # ocean mass transport along i-axis
            'sozohetr': '2D', # heat transport along i-axis
            'sozosatr': '2D', # salt transport along i-axis
            # V-grid
            'e3v': '3D', # V-cell thickness
            'vo': '3D', # ocean current along j-axis
            'vos': '2D', # ocean surface current along j-axis
            'tauvo': '2D', # wind stress along j-axis
            'vocetr_eff': '3D', # effective ocean volume transport along j-axis
            'vomematr': '3D', # ocean mass transport along j-axis
            'somehetr': '2D', # heat transport along j-axis
            'somesatr': '2D', # salt transport along j-axis
            # W-grid
            'e3w': '3D', # W-cell thickness
            'wo': '3D', # ocean vertical velocity (upward)
            'difvho': '3D', # vertical eddy diffusivity            
            #'vomematr': '3D', # vertical mass transport
            'av_wave': '3D', # internal wave-induced vertical diffusivity
            'bn2': '3D', # squared Brunt-Vaisala frequency
            'bflx_iwm': '3D', # internal wave-induced buoyancy flux
            'pcmap_iwm': '2D', # power consumption by wave-driven mixing
            'emix_iwm': '3D', # power density available for mixing
            'av_ratio ': '3D', # S over T diffusivity ratio
            # ice
        }

    return list

