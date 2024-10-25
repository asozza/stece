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
import shutil
import psutil
import logging
import argparse
import subprocess
import numpy as np
import xarray as xr
import cftime
from cdo import Cdo

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize CDO
cdo = Cdo()

# Define the correspondence between output & restart variables
varlists = {
    'thetao': ['tn', 'tb'],
    'so': ['sn', 'sb'],
    'zos': ['sshn', 'sshb'],
    'uo': ['un', 'ub'],
    'vo': ['vn', 'vb'],
    'rho': ['rhop']
}

year_zero = 1990

#######################################################################################

def get_memory_usage():
    """ get memory usage in MB """

    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()

    return mem_info.rss / (1024 ** 2)


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

#######################################################################################

def rebuild_nemo(expname, leg):
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

#######################################################################################

def _forecast_xarray(foreyear):
    """ Get the xarray for the forecast time """
    
    fdate = cftime.DatetimeGregorian(foreyear, 1, 1, 0, 0, 0, has_year_zero=False)
    xf = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])},
                      attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    return xf


def process_data(data, mode, dim='3D'):
    """
    Function for preprocessing or postprocessing 2D/3D data.

    Parameters:
    - data: xarray.DataArray or xarray.Dataset
        Input data to be processed.
    - mode: str
        Operation mode. Choose from:
        'pattern' - Preprocessing for EOF pattern.
        'timeseries' - Preprocessing for EOF timeseries.
        'postprocess' - Post-processing for variable field.
    - dim: str, optional (default='3D')
        Dimensionality of the dataset. Choose from '2D' or '3D'.

    Returns:
    - Processed data (xarray.DataArray or xarray.Dataset)
    """

    if dim not in {'2D', '3D'}:
        raise ValueError(f"Invalid dim '{dim}'. Choose '2D' or '3D'.")

    if mode == 'pattern':
        # Preprocessing routine for EOF pattern
        data = data.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
        data = data.rename({'nav_lat_grid_T': 'lat', 'nav_lon_grid_T': 'lon'})
        data = data.rename({'time_counter': 'time'})
        data = data.drop_vars({'time_counter_bnds'}, errors='ignore')
        if dim == '3D':
            data = data.rename({'deptht': 'z'})
            data = data.drop_vars({'deptht_bnds'}, errors='ignore')        

    elif mode == 'tseries':
        # Preprocessing routine for EOF timeseries
        data = data.rename({'time_counter': 'time'})
        data = data.isel(lon=0, lat=0)
        data = data.drop_vars({'time_counter_bnds', 'lon', 'lat'}, errors='ignore')
        if dim == '3D':
            data = data.isel(zaxis_Reduced=0)
            data = data.drop_vars({'zaxis_Reduced'}, errors='ignore')

    elif mode == 'postproc':
        # Post-processing routine for variable field
        data = data.rename({'time': 'time_counter'})
        if dim == '3D':
            data = data.rename({'z': 'nav_lev'})

    else:
        raise ValueError(f"Invalid mode '{mode}'. Choose from 'pattern', 'tseries', or 'postproc'.")

    return data

#######################################################################################


def merge_winter_only(expname, varname, startyear, endyear):
    """
    Process NEMO output files to focus on winter months (December and January),
    calculate a moving average, and merge the results using xarray and CDO.

    Parameters:
    - expname: experiment name.
    - startyear: the starting year of the time window.
    - endyear: the ending year of the time window.
    - var: variable name to process.
    - dirs: dictionary containing directory paths ('nemo' for input, 'tmp' for temporary files).
    """

    # Load the data with xarray
    files = []
    for year in range(startyear, endyear + 1):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}.nc")
        files.extend(glob.glob(pattern))

    # Combine all files into a single dataset
    ds = xr.open_mfdataset(files, combine='by_coords')

    # Select the variable and group by month to filter December and January
    ds_var = ds[varname]

    # Group by month and filter out only December (12) and January (1)
    ds_winter = ds_var.groupby('time.month').filter(lambda x: x.month in [12, 1])

    # Remove the first January and the last December
    ds_winter = ds_winter.where(~((ds_winter['time.month'] == 1) & (ds_winter['time.year'] == startyear)), drop=True)
    ds_winter = ds_winter.where(~((ds_winter['time.month'] == 12) & (ds_winter['time.year'] == endyear)), drop=True)

    # Calculate a moving average with a window of 2 months (for Dec-Jan pairs)
    ds_winter_avg = ds_winter.rolling(time=2, center=True).mean().dropna('time', how='all')

    # Save file
    temp_file = os.path.join(dirs['tmp'], f"{varname}_winter_{startyear}_{endyear}_temp.nc")
    final_file = os.path.join(dirs['tmp'], f"{varname}_winter_{startyear}_{endyear}.nc")
    ds_winter_avg.to_netcdf(temp_file)

    # perform CDO time mean
    cdo.timmean(input=temp_file, output=final_file)

    # Remove the temporary file
    os.remove(temp_file)

    return final_file


def detrend(expname, varname, leg):
    """Detrend data by subtracting the time average using the CDO Python package."""
    
    dirs = folders(expname)
    varfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}.nc")
    anomfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_anomaly.nc")
    try:
        os.remove(anomfile)
        logging.info(f"File {anomfile} successfully removed.")
    except FileNotFoundError:
        logging.info(f"File {anomfile} not found.")

    logging.info(f"Detrending variable {varname} by subtracting the time average.")
    
    # Detre             nding using CDO: subtract the time mean from the variable
    cdo.sub(input=[varfile, f"-timmean {varfile}"], output=anomfile)

    return None


def get_EOF(expname, varname, leg, window):
    """Compute EOF using the CDO Python package with error handling."""

    # Get the directories and file paths
    dirs = folders(expname)

    # Define file paths for anomaly, covariance, and pattern output files
    flda = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_anomaly.nc")
    
    fldcov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_variance.nc")
    try:
        os.remove(fldcov)
        logging.info(f"File {fldcov} successfully removed.")
    except FileNotFoundError:
        logging.info(f"File {fldcov} not found.")

    fldpat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_pattern.nc")
    try:
        os.remove(fldpat)
        logging.info(f"File {fldpat} successfully removed.")
    except FileNotFoundError:
        logging.info(f"File {fldpat} not found.")

    logging.info(f"Computing EOF for variable {varname} with window size {window}.")
    
    # CDO command to compute EOFs
    cdo.eof3d(window, input=flda, output=fldcov)
    
    # Compute EOF patterns
    cdo.eof3d(window, input=flda, output=fldpat)

    # Define timeseries output file pattern
    timeseries = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_series_")
    try:
        os.remove(timeseries)
        logging.info(f"File {timeseries} successfully removed.")
    except FileNotFoundError:
        logging.info(f"File {timeseries} not found.")

    # Compute EOF coefficients (timeseries)
    logging.info(f"Computing EOF coefficients for {varname}.")
    cdo.eofcoeff3d(input=[fldpat, flda], output=timeseries)

    logging.info(f"EOF computation completed successfully: {fldcov}, {fldpat}, {timeseries}")
    
    return None


def add_smoothing(input, output):
    """ add smoothing """

    cdo.smooth9("radius=2deg", input=input, output=output)

    return None

#######################################################################################


def constraints(data):
    """ Check and apply constraints to variables: U < 10 m/s, |ssh| < 20 m, S in [0,100] psu, T > -2.5 degC """ 

    # for horizontal velocity (u,v)
    for var in ['un', 'ub', 'vn', 'vb']:
        if var in data:
            data[var] = xr.where(data[var] > 10, 10, data[var])  # Ensure U < 10 m/s
    
    # for sea surface height (ssh)
    for var in ['sshn', 'sshb']:
        if var in data:
            data[var] = xr.where(np.abs(data[var]) > 20, 20 * np.sign(data[var]), data[var])  # Ensure |ssh| < 20
    
    # for salinity
    for var in ['sn', 'sb']:
        if var in data:
            data[var] = data[var].clip(0, 100)  # Ensure S in [0, 100]
    
    # for temperature
    for var in ['tn', 'tb']:
        if var in data:
            data[var] = xr.where(data[var] < -2.5, -2.5, data[var])  # Ensure T > -2.5

    return data


#######################################################################################


def forecast_nemo(expname, varnames, endleg, yearspan, yearleap, reco=False):
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

    # create EOF
    for varname in varnames:
    
        merge_winter_only(expname, varname, startyear, endyear, window)
        detrend()

        # load pattern
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_pattern.nc")
        pattern = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, mode='pattern', dim='3D'))
        field = pattern.isel(time=0)*0

        # loop on EOF timeseries
        for i in range(window):
            # load data EOF timeseries
            filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_series_0000{i}.nc")    
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, mode='timeseries', dim='3D'))

            # variable projection based on 'reco' flag
            if reco == False:
                p = timeseries.polyfit(dim='time', deg=1, skipna = True)
                theta = xr.polyval(xf, p[f"{varname}_polyfit_coefficients"])
            else:
                theta = timeseries[varname].isel(time=-1)

            # Accumulate the field using the basis from the pattern
            basis = pattern.isel(time=i)
            field = field + theta*basis

        # If reco is False, drop the 'time' variable
        if not reco:
            field = field.drop_vars({'time'}, errors='ignore')

        # Retrend: Load the full dataset and compute the time mean
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}.nc")
        xdata = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, mode='pattern', dim='3D'))
        ave = xdata[varname].mean(dim=['time'])  # Time mean
        total = field + ave  # Add the mean to the field

        # Apply post-processing to the total field
        total = process_data(total, mode='postprocess', dim='3D')

        # Assign 'time_counter' to the final result
        total['time_counter'] = rdata['time_counter']

        # loop on the corresponding varlist    
        varlist = varlists.get(varname, []) # Get the corresponding varlist, default to an empty list if not found
        for vars in varlist:
            rdata[vars] = xr.where(rdata[vars] != 0.0, total[varname], 0.0)

    return rdata

#######################################################################################


def write_restart(expname, rdata, leg):
    """ Write NEMO restart file in a temporary folder """

    dirs = folders(expname)
    flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + 'restart' + '_????.nc'))
    timestep = os.path.basename(flist[0]).split('_')[1]

    # ocean restart creation
    oceout = os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart.nc')
    rdata.to_netcdf(oceout, mode='w', unlimited_dims={'time_counter': True})

    # copy ice restart
    orig = os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '_' + timestep + '_restart_ice.nc')
    dest = os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart_ice.nc')
    shutil.copy(orig, dest)

    return None


def replace_restart(expname, leg):
    """ Replace modified restart files in the run folder """

    dirs = folders(expname)

    # cleaning
    browser = ['restart*.nc']
    for basefile in browser:
        filelist = sorted(glob.glob(os.path.join(dirs['exp'], basefile)))
        for file in filelist:
            if os.path.isfile(file):
                print('Removing' + file)
                os.remove(file)

    # create new links
    browser = ['restart.nc', 'restart_ice.nc']
    for file in browser:
        rebfile = os.path.join(dirs['tmp'], str(leg).zfill(3), file)
        resfile = os.path.join(dirs['restart'], str(leg).zfill(3), file)
        shutil.copy(rebfile, resfile)
        newfile = os.path.join(dirs['exp'], file)
        print("Linking rebuilt NEMO restart", file)            
        os.symlink(resfile, newfile)
    
    return None

#######################################################################################


def parse_args():
    """ Command line parser for nemo-restart """

    parser = argparse.ArgumentParser(description="Command Line Parser for NEMO forecast")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("leg", metavar="LEG", help="Leg of rebuilding", type=int)
    parser.add_argument("yearspan", metavar="YEARSPAN", help="Year span for EOF", type=int)
    parser.add_argument("yearleap", metavar="YEARLEAP", help="Year leap in the future", type=int)

    # optional to activate nemo rebuild
    parser.add_argument("--rebuild", action="store_true", help="Enable NEMO rebuild")
    parser.add_argument("--forecast", action="store_true", help="Create NEMO forecast")
    parser.add_argument("--replace", action="store_true", help="Replace NEMO restarts")

    parsed = parser.parse_args()

    return parsed


#######################################################################################
# MAIN 
#######################################################################################
if __name__ == "__main__":
    
    # parser
    args = parse_args()
    expname = args.expname
    leg = args.leg
    yearspan = args.yearspan
    yearleap = args.yearleap

    # initiate time clock
    start_time = time.time()

    # define folders
    dirs = folders(expname)

    # rebuild nemo restart files
    if args.rebuild:
        rebuild_nemo(expname, leg)
    
    varnames = ['thetao', 'so']

    # forecast
    if args.forecast:
        rdata = forecast_nemo(expname, varnames, leg, yearspan, yearleap)
        write_restart(expname, rdata, leg)

    # replace nemo restart files
    if args.replace:
        replace_restart(expname, leg)

    # ending timer and get memory usage
    end_time = time.time()
    execution_time = end_time - start_time
    memory_usage = get_memory_usage()
    logging.info(f"Total execution time: {execution_time:.2f} seconds")
    logging.info(f"Memory load at the end: {memory_usage:.2f} MB")
