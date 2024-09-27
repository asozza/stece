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

import logging
from dask.distributed import LocalCluster, Client, progress
from dask.distributed.diagnostics import MemorySampler

from osprey.graphics.timeseries import timeseries


def parse_args():
    """Command line parser for graphics"""

    parser = argparse.ArgumentParser(description="Command line parser for graphics")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="expname", help="Experiment name", type=str)
    parser.add_argument("startyear", metavar="startyear", help="start year", type=int)
    parser.add_argument("endyear", metavar="endyear", help="end year", type=int)
    parser.add_argument("varlabel", metavar="varlabel", help="Variable label", type=str)
    #parser.add_argument("reader", metavar="reader", help="reader", type=str)    
    #parser.add_argument("metric", metavar="metric", help="metric", type=str)    
    #parser.add_argument("replace", metavar="replace", help="replace", type=bool)    
    #parser.add_argument("rescale", metavar="rescale", help="rescale", type=bool)    
    #parser.add_argument("avetype", metavar="avetype", help="average type", type=str)    
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
    #reader = args.reader
    #metric = args.metric
    #replace = args.replace
    #rescale = args.rescale
    #avetype = args.avetype
    figname = args.figname

    # color= args.color
    # linestyle = args.linestyle
    # marker = args.marker
    # label = args.label
    # ax = args.ax

    # open cluster
    cluster = LocalCluster(n_workers=2, threads_per_worker=1, memory_limit='8GB')
    client = Client(cluster)

    opus = timeseries(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, 
               reader='nemo', metric='base', replace=False, rescale=False, avetype='standard', 
               figname=figname)
    
    # memory monitoring is always operating
    ms = MemorySampler()
    array_data = np.array(vars(ms)['samples']['chunk'])
    avg_mem = np.mean(array_data[:, 1])/1e9
    max_mem = np.max(array_data[:, 1])/1e9
    client.shutdown()
    cluster.close()
    logging.warning('Avg memory used: %.2f GiB, Peak memory used: %.2f GiB', avg_mem, max_mem)

