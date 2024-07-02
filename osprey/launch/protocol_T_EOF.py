#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a command line tool to modfy the NEMO restart files from a specific EC-Eart4
experiment, given a specific experiment and leg. 

Needed modules:
# module load intel/2021.4.0 intel-mkl/19.0.5 prgenv/intel hdf5 netcdf4 
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/apps/netcdf4/4.9.1/INTEL/2021.4/lib:/usr/local/apps/hdf5/1.12.2/INTEL/2021.4/lib

Authors
Alessandro Sozza and Paolo Davini (CNR-ISAC, May 2024)
"""

import argparse
import xarray as xr

from osprey.utils.folders import folders
from osprey.actions.rebuilder import rebuilder
from osprey.actions.forecaster import forecaster_EOF
from osprey.actions.writer import writer_restart
from osprey.actions.replacer import replacer


def parse_args():
    """Command line parser for nemo-restart"""

    parser = argparse.ArgumentParser(description="Command Line Parser for nemo-restart")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("leg", metavar="LEG", help="The leg you want to process for rebuilding", type=int)
    parser.add_argument("yearspan", metavar="YEARSPAN", help="Year span for fitting temperature", type=int)
    parser.add_argument("yearleap", metavar="YEARLEAP", help="Year leap for projecting temperature", type=int)

    # optional to activate nemo rebuild
    parser.add_argument("--rebuild", action="store_true", help="Enable nemo-rebuild")    
    parser.add_argument("--replace", action="store_true", help="Replace nemo restart files")

    parsed = parser.parse_args()

    return parsed

if __name__ == "__main__":
    
    # parser
    args = parse_args()
    expname = args.expname
    leg = args.leg
    yearspan = args.yearspan
    yearleap = args.yearleap

    # define folders
    dirs = folders(expname)

    # rebuild nemo restart files
    if args.rebuild:
        rebuilder(expname, leg)
    
    # forecast based on local temperature fit
    #rdata = forecaster_EOF(expname, 'thetao', '3D', leg, yearspan, yearleap)
    #writer_restart(expname, rdata, leg)

    # replace nemo restart files
    if args.replace:
        replacer(expname, leg)

