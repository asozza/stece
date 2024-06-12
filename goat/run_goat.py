#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
This is a command line tool to run GOAT diagnostics.

Needed modules:
# module load intel/2021.4.0 intel-mkl/19.0.5 prgenv/intel hdf5 netcdf4 
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/apps/netcdf4/4.9.1/INTEL/2021.4/lib:/usr/local/apps/hdf5/1.12.2/INTEL/2021.4/lib

Authors
Alessandro Sozza (CNR-ISAC, May 2024)
"""


import numpy as np
import xarray as xr
import argparse
import matplotlib.pyplot as plt
import goat_plots as gp
import goat_io as io
import goat_tools as gt
import goat_means as gm
import goat_graphs as gg


def parse_args():
    """Command line parser for rebuild_nemo"""

    parser = argparse.ArgumentParser(description="Command Line Parser for rebuild_nemo")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("startyear", metavar="STARTYEAR", help="Start year")
    parser.add_argument("endyear", metavar="ENDYEAR", help="End year")
    parser.add_argument("var", metavar="VAR", help="Variable name")
    parser.add_argument("ndim", metavar="NDIM", help="Dimensions")
    parser.add_argument("norm", metavar="NORM", help="Normalization")
    parser.add_argument("idx_norm", metavar="IDX_NORM", help="Normalization index")
    parser.add_argument("idx_ave", metavar="IDX_AVE", help="Averaging index")
    parser.add_argument("offset", metavar="OFFSET", help="Offset")
    parser.add_argument("color", metavar="COLOR", help="Color")

    parsed = parser.parse_args()

    return parsed

if __name__ == "__main__":
    
     # parser
    args = parse_args()
    expname = args.expname
    startyear = args.startyear
    endyear = args.endyear
    var = args.var
    ndim = args.ndim
    norm = args.norm
    idx_norm = args.idx_norm
    idx_ave = args.idx_ave
    offset = args.offset
    color = args.color

    gg.timeseries(expname, startyear, endyear, var, ndim, norm, idx_norm, idx_ave, offset, color)



