#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a command line tool for applying the forecast

Needed modules:
# module load intel/2021.4.0 intel-mkl/19.0.5 prgenv/intel hdf5 netcdf4 
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/apps/netcdf4/4.9.1/INTEL/2021.4/lib:/usr/local/apps/hdf5/1.12.2/INTEL/2021.4/lib

Authors: Alessandro Sozza (CNR-ISAC)
Date: Oct 2024
"""

import os
import glob
import time
import psutil
import logging
import argparse
import subprocess
import numpy as np
import xarray as xr
import cftime

from osprey.utils.folders import folders
from osprey.actions.rebuilder import rebuilder
from osprey.actions.forecaster import forecaster_EOF_winter_multivar
from osprey.actions.writer import writer_restart
from osprey.actions.replacer import replacer, restorer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Function to get memory usage in MB
def get_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 2)  # Convert bytes to megabytes (MB)


def folders(expname):
    """ List of global paths dependent on expname """

    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'nemo': os.path.join("/ec/res4/scratch/itas/ece4", expname, "output", "nemo"),
        'oifs': os.path.join("/ec/res4/scratch/itas/ece4", expname, "output", "oifs"),
        'restart': os.path.join("/ec/res4/scratch/itas/ece4", expname, "restart"),     
        'tmp':  os.path.join("/ec/res4/scratch/itas/martini", expname),
        'rebuild': "/ec/res4/hpcperm/itas/src/rebuild_nemo"
    }

    return dirs


def rebuilder(expname, leg):
    """ Function to rebuild NEMO restart """

    dirs = folders(expname)
    
    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)

    rebuild_exe = os.path.join(dirs['rebuild'], "rebuild_nemo")
  
    for kind in ['restart', 'restart_ice']:
        print(' Processing ' + kind)
        flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + kind + '_????.nc'))
        tstep = os.path.basename(flist[0]).split('_')[1]

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], str(leg).zfill(3), os.path.basename(filename))
            try:
                os.symlink(filename, destination_path)
            except FileExistsError:
                pass

        rebuild_command = [rebuild_exe, "-m", os.path.join(dirs['tmp'], str(leg).zfill(3), expname + "_" + tstep + "_" + kind ), str(len(flist))]
        try:
            subprocess.run(rebuild_command, stderr=subprocess.PIPE, text=True, check=True)
            for file in glob.glob('nam_rebuld_*'):
                os.remove(file)
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            print(error_message)

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], str(leg).zfill(3), os.path.basename(filename))
            os.remove(destination_path)

    flist = glob.glob('nam_rebuild*')
    for file in flist:
        os.remove(file)

    return None


def _forecast_xarray(foreyear):
    """ Get the xarray for the forecast time """
    
    fdate = cftime.DatetimeGregorian(foreyear, 1, 1, 0, 0, 0, has_year_zero=False)
    xf = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])},
                      attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    return xf


def preproc_pattern_3D(data):
    """ Preprocessing routine for EOF pattern """

    data = data.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
    data = data.rename({'nav_lat_grid_T': 'lat', 'nav_lon_grid_T': 'lon'})
    data = data.rename({'time_counter': 'time', 'deptht': 'z'})
    data = data.drop_vars({'time_counter_bnds', 'deptht_bnds'})
    
    return data


def preproc_timeseries_3D(data):
    """ Preprocessing routine for EOF timeseries """

    data = data.rename({'time_counter': 'time'})
    data = data.isel(lon=0,lat=0,zaxis_Reduced=0)
    data = data.drop_vars({'time_counter_bnds','lon','lat','zaxis_Reduced'})

    return data


def postproc_var_3D(data):
    """ Post-processing routine for variable field """

    data = data.rename({'time': 'time_counter', 'z': 'nav_lev'})

    return data


def get_EOF_winter():
    """ from data to EOF """

    return None


def forecaster(expname, varnames, endleg, yearspan, yearleap, reco=False):
    """ 
    Function to forecast winter temperature field using EOF 
    
    Args:
    expname: experiment name
    varname: variable name
    endleg: leg 
    yearspan: years backward from endleg used by EOFs
    yearleap: years forward from endleg to forecast
    reco: reconstruction of present time
    
    """

    dirs = folders(expname)

    year_zero = 1990
    startleg = endleg - yearspan + 1 
    startyear = year_zero + endleg - 1
    endyear = year_zero + endleg -1
    window = endyear - startyear + 1

    # forecast year
    foreyear = (endyear + yearleap)
    xf = _forecast_xarray(foreyear)

    # read forecast and change restart
    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), expname + '*_restart.nc')
    logging.info(' File to be loaded %s', filename)
    rdata = xr.open_mfdataset(filename, use_cftime=True)

    # Define the varlists for each variable
    varlists = {
        'thetao': ['tn', 'tb'],
        'so': ['sn', 'sb'],
        'zos': ['sshn', 'sshb']
    }

    # create EOF
    for varname in varnames:
    
        get_EOF_winter(expname, varname, startyear, endyear, window)
    
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_pattern.nc")
        pattern = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_pattern_3D)
        field = pattern.isel(time=0)*0
        for i in range(window):
            filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_series_0000{i}.nc")    
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_timeseries_3D)
            if reco == False:
                p = timeseries.polyfit(dim='time', deg=1, skipna = True)
                theta = xr.polyval(xf, p[f"{varname}_polyfit_coefficients"])
            else:
                theta = timeseries[varname].isel(time=-1)
            basis = pattern.isel(time=i)
            field = field + theta*basis

        if reco ==  False:   
            field = field.drop_vars({'time'})

        # retrend
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}.nc")
        xdata = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_pattern_3D)
        ave = xdata[varname].mean(dim=['time']) # time mean
        total = field + ave

        #if reco == False:
        #    total = total.expand_dims({'time': 1})
        total = postproc_var_3D(total)
        total['time_counter'] = rdata['time_counter']

        # loop on the corresponding varlist    
        varlist = varlists.get(varname, []) # Get the corresponding varlist, default to an empty list if not found
        for vars in varlist:
            rdata[vars] = xr.where(rdata[vars] != 0.0, total[varname], 0.0)

    return rdata


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
    parser.add_argument("--forecast", action="store_true", help="Create forecast")
    parser.add_argument("--replace", action="store_true", help="Replace nemo restart files")
    parser.add_argument("--restore", action="store_true", help="Restore nemo restart files")

    parsed = parser.parse_args()

    return parsed

# ########################
#
# MAIN 
#
# ########################
if __name__ == "__main__":
    
    # parser
    args = parse_args()
    expname = args.expname
    leg = args.leg
    yearspan = args.yearspan
    yearleap = args.yearleap

    # Initiate time clock
    start_time = time.time()

    # define folders
    dirs = folders(expname)

    # rebuild nemo restart files
    if args.rebuild:
        rebuilder(expname, leg)
    
    varnames = ['thetao', 'so']

    # forecast based on local temperature fit
    if args.forecast:
        rdata = forecaster(expname, varnames, leg, yearspan, yearleap)
        writer_restart(expname, rdata, leg)

    # replace nemo restart files
    if args.replace:
        replacer(expname, leg)

    if args.restore:
        restorer(expname, leg)


    # Ending timer and get memory usage
    end_time = time.time()
    execution_time = end_time - start_time
    memory_usage = get_memory_usage()
    # Log execution time and memory load
    logging.info(f"Total execution time: {execution_time:.2f} seconds")
    logging.info(f"Memory load at the end: {memory_usage:.2f} MB")