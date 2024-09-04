#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command line tool to modify the NEMO restart files from a EC-Eart4 experiment, given a specific experiment name and time leg. 

Needed modules:
# module load intel/2021.4.0 intel-mkl/19.0.5 prgenv/intel hdf5 netcdf4
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/apps/netcdf4/4.9.1/INTEL/2021.4/lib:/usr/local/apps/hdf5/1.12.2/INTEL/2021.4/lib

Authors: Alessandro Sozza and Paolo Davini (CNR-ISAC)
Date: Nov 2023
"""

import argparse
from osprey.actions.rebuilder import rebuilder

def parse_args():
    """Command line parser for rebuild_nemo"""

    parser = argparse.ArgumentParser(description="Command Line Parser for rebuild_nemo")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("leg", metavar="LEG", help="Time leg", type=str)
    parsed = parser.parse_args()

    return parsed

if __name__ == "__main__":
    
     # parser
    args = parse_args()
    expname = args.expname
    leg = args.leg

    rebuilder(expname, leg)
