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
            'thetao' : '3D',
            'so': '3D',
            'tos': '2D',
            'sos': '2D',
            'zos': '2D',
            'sbt': '2D',
            'heatc': '2D',
            'saltc': '2D',
            'qsr_oce': '2D',
            'qns_oce': '2D',
            'qt_oce': '2D',
            'sfx': '2D'
        }

    return list

