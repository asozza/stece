#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project a desired variable (e.g. thetao, tos, heat content) in the future by linear regression

Authors
Alessandro Sozza (CNR-ISAC, Oct 2023)
"""

import subprocess
import os
import glob
import shutil
import argparse
import xarray as xr

def parse_args():
    """Command line parser for future_linear"""

    parser = argparse.ArgumentParser(description="Command Line Parser for future_linear")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("varname", metavar="VARNAME", help="Variable to project in the future")
    parser.add_argument("futtime", metavar="FUTTIME", help="Future time in YYYY-MM-DD", type=str)
    
    parsed = parser.parse_args()

    return parsed

def linear_regress(Xd, Yd, futtime):
    model=LinearRegression()
    model.fit(Xd, Yd)
    mp = model.coef_[0][0]
    qp = model.intercept_[0]
    Y_pred = model.predict([[futtime]])
    return Y_pred

if __name__ == "__main__":
    
    # parser
    args = parse_args()
    expname = args.expname
    varname = args.varname
    futtime = args.futtime

     # define directories
    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'tmp':  os.path.join("/lus/h2resw01/scratch/itas/martini", expname, leg.zfill(3)),
        'rebuild': "/ec/res4/hpcperm/itas/src/rebuild_nemo"
    }
