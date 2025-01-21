#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reader module

Author: Alessandro Sozza
Date: Dec 2024
"""

import os
import glob
import logging
import xarray as xr

from osprey.utils import config
from osprey.utils import catalogue


##########################################################################################
# Reader of NEMO domain

def preproc_nemo_domain(data):
    """ Pre-processing routine for nemo domain """

    data = data.rename({'time_counter': 'time'})

    return data

def read_domain(orca):
    """ Read NEMO domain configuration file """

    dirs = config.paths()
    filename = os.path.join(dirs['domain'], orca, 'domain_cfg.nc')
    domain = xr.open_mfdataset(filename, preprocess=preproc_nemo_domain)
    domain = domain.isel(time=0)

    return domain

def elements(orca):
    """ Define differential forms for integrals """

    df = {}
    domain = read_domain(orca)
    df['V'] = domain['e1t']*domain['e2t']*domain['e3t_0']
    df['S'] = domain['e1t']*domain['e2t']
    df['x'] = domain['e1t']
    df['y'] = domain['e2t']
    df['z'] = domain['e3t_0']

    return df

##########################################################################################
