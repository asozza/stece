#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Space module

Author: Alessandro Sozza (CNR-ISAC) 
Date: June 2024
"""

import os
import yaml
import numpy as np
import datetime
import time


def flatten_to_triad(m, nj, ni):
    """ Recover triad indexes from flatten array length """

    k = m // (ni * nj)
    j = (m - k * ni * nj) // ni
    i = m - k * ni * nj - j * ni

    return k, j, i


def subregions(idx, orca):
    """     
    Definition of vertical subregions for ORCAs 
    mixed layer (0-100 m), pycnocline (100-1000 m), abyss (1000-5000 m)
    levels in ORCA2: [0,9] [10,20] [21,30]
    levels in eORCA1: [0,23] [24,45] [46,74]

    Args:
        idx (string): mix, pyc, aby
        orca (string): ORCA2,eORCA1
            
    """

    if orca == 'ORCA2':
        if idx == 'mix':
            z1 = 0; z2 = 9
        elif idx == 'pyc':
            z1 = 10; z2 = 20
        elif idx == 'aby':
            z1 = 21; z2 = 30
        else:
            raise ValueError(" Invalid subrange ")
    elif orca == 'eORCA1':
        if idx == 'mix':
            z1 = 0; z2 = 23
        elif idx == 'pyc':
            z1 = 24; z2 = 45
        elif idx == 'aby':
            z1 = 46; z2 = 74
        else:
            raise ValueError(" Invalid subrange ")
    else:
        raise ValueError(" Invalid ORCA grid ")
    
    return z1,z2


