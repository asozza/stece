#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a command line tool to plot graphics

Authors: Alessandro Sozza (CNR-ISAC)
Date: Sept 2024
"""

import argparse
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from osprey.graphics.timeseries import timeseries


def parse_args():
    """Command line parser for nemo-restart"""

    parser = argparse.ArgumentParser(description="Command line parser for graphics")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="expname", help="Experiment name", type=str)
    parser.add_argument("startyear", metavar="startyear", help="start year", type=int)
    parser.add_argument("endyear", metavar="endyear", help="end year", type=int)
    parser.add_argument("varlabel", metavar="varlabel", help="Variable label", type=str)
    parser.add_argument("figname", metavar="figname", help="Figure name", type=str)

    parsed = parser.parse_args()

    return parsed

if __name__ == "__main__":
    
    # parser
    args = parse_args()
    expname = args.expname
    startyear = args.startyear
    endyear = args.endyear
    varlabel = args.varlabel
    figname = args.figname

    timeseries(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, figname=figname)
