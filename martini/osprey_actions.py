#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Osprey library for actions

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import subprocess
import numpy as np
import os
import glob
import shutil
import yaml
import dask
import cftime
import nc_time_axis
import xarray as xr
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
import osprey_io as osi
import osprey_means as osm
import osprey_tools as ost
import osprey_checks as osc
import osprey_eof as ose

def rebuilder(expname, leg):
    """ Function to rebuild NEMO restart """

    dirs = osi.folders(expname)
    
    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)

    rebuilder = os.path.join(dirs['rebuild'], "rebuild_nemo")
  
    for kind in ['restart', 'restart_ice']:
        print(' Processing ' + kind)
        flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + kind + '_????.nc'))
        tstep = ost.get_nemo_timestep(flist[0])

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], str(leg).zfill(3), os.path.basename(filename))
            try:
                os.symlink(filename, destination_path)
            except FileExistsError:
                pass

        rebuild_command = [rebuilder, "-m", os.path.join(dirs['tmp'], str(leg).zfill(3), expname + "_" + tstep + "_" + kind ), str(len(flist))]
        try:
            subprocess.run(rebuild_command, stderr=subprocess.PIPE, text=True, check=True)
            for file in glob.glob('nam_rebuld_*') : 
                os.remove(file)
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            print(error_message) 

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], str(leg).zfill(3), os.path.basename(filename))
            os.remove(destination_path)

    # read timestep
    #filelist = glob.glob(os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart.nc'))    
    #timestep = ost.get_nemo_timestep(filelist[0])

    # copy restart
    #shutil.copy(os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '_' + timestep + '_restart.nc'), os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart.nc'))
    #shutil.copy(os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '_' + timestep + '_restart_ice.nc'), os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart_ice.nc'))

    # remove 
    #os.remove(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart.nc'))
    #os.remove(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart_ice.nc'))

    flist = glob.glob('nam_rebuild*')
    for file in flist:
        os.remove(file)

    return None

def rollbacker(expname, leg):
    """ Function to rollback ECE4 run to a previous leg """

    # define directories
    dirs = osi.folders(expname)

    # cleaning
    # create list of files to be remove in the run folder
    browser = ['rstas.nc', 'rstos.nc',  'srf000*.????', 'restart*.nc', 'rcf']
    for file in browser:
        filelist = sorted(glob.glob(os.path.join(dirs['exp'], file)))
        for file in filelist:
            if os.path.isfile(file):
                print('Removing' + file)
                os.remove(file)

    # update time.step
    flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + 'restart' + '_????.nc'))
    timestep = ost.get_nemo_timestep(flist[0])
    tstepfile = os.path.join(dirs['exp'], 'time.step')
    with open(tstepfile, 'w', encoding='utf-8') as file:
        file.write(str(int(timestep)))

    # update the leginfo rolling back to the require leg
    legfile = os.path.join(dirs['exp'], 'leginfo.yml')
    with open(legfile, 'r', encoding='utf-8') as file:
        leginfo = yaml.load(file, Loader=yaml.FullLoader)

    # get new date
    info = leginfo['base.context']['experiment']['schedule']['leg']
    deltaleg = int(leg) - info['num']    
    newdate = info['start'] + relativedelta(years=deltaleg)
    orgdate = info['start']

    # modify the file only if it is necessary
    if int(leg) < info['num']:

        #print(info['start'] + relativedelta(years=deltayear))        
        leginfo['base.context']['experiment']['schedule']['leg']['start'] = newdate
        leginfo['base.context']['experiment']['schedule']['leg']['num'] = int(leg)
        
        print("Updating the leginfo to leg number " + leg)
        with open(legfile, 'w', encoding='utf8') as outfile:
            yaml.dump(leginfo, outfile, default_flow_style=False)

    elif int(leg) == info['num']:
        print("Nothing to do on the leginfo.yaml")
    else:
        raise ValueError("I cannot go forward in time...")

    # copying from the restart folder required for the leg you asked
    browser = ['rstas.nc', 'rstos.nc',  'srf000*.????', 'rcf', '*restart*']
    for file in browser:
        filelist = sorted(glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), file)))
        for file in filelist:
            basefile = os.path.basename(file)
            targetfile = os.path.join(dirs['exp'], basefile)
            if not os.path.isfile(targetfile):
                # copy rcf and oasis file
                if basefile in ['rstas.nc', 'rstos.nc', 'rcf']:
                    print("Copying restart", file)
                    shutil.copy(file, targetfile)
                # link oifs files
                elif 'srf' in basefile:
                    print("Linking IFS restart", file)
                    os.symlink(file, targetfile)
                # link and rename nemo files
                elif 'restart' in basefile:
                    newfile = os.path.join(dirs['exp'], '_'.join(basefile.split('_')[2:]))
                    print("Linking NEMO restart", file)
                    os.symlink(file, newfile)

    # removing old output to avoid mess
    browser = list(range(newdate.year, orgdate.year))
    for year in browser:
        filelist = sorted(glob.glob(os.path.join(dirs['exp'],  'output', '*', '*' + str(year) + '*')))
        for file in filelist:
            if os.path.isfile(file):
                print('Removing output file', file)
                os.remove(file)

    return None


def replacer(expname, leg):
    """ Function to replace modified restart files in the run folder """

    dirs = osi.folders(expname)

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


def forecaster_fit(expname, var, endleg, yearspan, yearleap):
    """ Function to forecast local temperature using linear fit of output files """

    # get time interval
    endyear = ost.get_year(endleg)
    startleg = ost.get_startleg(endleg, yearspan)
    startyear = ost.get_startyear(endyear, yearspan)

    # get forecast year
    foreyear = ost.get_forecast_year(endyear,yearleap)
    fdate = cftime.DatetimeGregorian(foreyear, 1, 1, 12, 0, 0, has_year_zero=False)
    xf = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])}, attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    # load data
    data = osi.read_T(expname, startyear, endyear)

    # fit
    p = data[var].polyfit(dim='time', deg=1, skipna=True)
    yf = xr.polyval(xf, p.polyfit_coefficients)
    yf = yf.rename({'time': 'time_counter', 'z': 'nav_lev'})
    yf = yf.drop_indexes({'x', 'y'})
    yf = yf.reset_coords({'x', 'y'}, drop=True)
    
    rdata = osi.read_rebuilt(expname, endleg, endleg)
    varlist = ['tn', 'tb']
    for var1 in varlist:
        rdata[var1] = xr.where(rdata[var1] !=0, yf.values, 0.0)

    return rdata


def forecaster_fit_re(expname, var, endleg, yearspan, yearleap):
    """ Function to forecast local temperature using linear fit of restart files """

    # get time interval
    endyear = ost.get_year(endleg)
    startleg = ost.get_startleg(endleg, yearspan)
    startyear = ost.get_startyear(endyear, yearspan)

    # get forecast year
    foreyear = ost.get_forecast_year(endyear,yearleap)
    fdate = cftime.DatetimeGregorian(foreyear, 1, 1, 12, 0, 0, has_year_zero=False)
    xf = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])}, attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    # load restarts
    rdata = osi.read_restart(expname, startyear, endyear)

    # fit
    yf = {}
    varlist = ['tn', 'tb']
    for vars in varlist:   
        p = rdata[var].polyfit(dim='time', deg=1, skipna=True)
        yf[vars] = xr.polyval(xf, p.polyfit_coefficients)
    yf = yf.rename({'time': 'time_counter', 'z': 'nav_lev'})
    yf = yf.drop_indexes({'x', 'y'})
    yf = yf.reset_coords({'x', 'y'}, drop=True)

    rdata = osi.read_rebuilt(expname, endleg, endleg)
    for vars in varlist: 
        #yf[var] = yf[var].where( yf < -1.8, rdata[var], yf[var])
        rdata[vars] = yf[vars]

    return rdata

# add vfrac: percetuage of EOF to consider: 1.0 -> all
def forecaster_EOF(expname, var, ndim, endleg, yearspan, yearleap):
    """ Function to forecast temperature field using EOF """

    dirs = osi.folders(expname)
    startleg = ost.get_startleg(endleg, yearspan)
    startyear = ost.get_year(startleg)
    endyear = ost.get_year(endleg)
    window = endyear - startyear

    # forecast year
    foreyear = ost.get_forecast_year(endyear, yearleap)
    fdate = cftime.DatetimeGregorian(foreyear, 7, 1, 12, 0, 0, has_year_zero=False)
    foredate = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])}, attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    # create EOF
    ose.cdo_merge(expname, startyear, endyear)
    ose.cdo_selname(expname, startyear, endyear, var)
    ose.cdo_detrend(expname, startyear, endyear, var)
    ose.cdo_EOF(expname, startyear, endyear, var, ndim)
    
    if ndim == '2D':
        pattern = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_pattern_{startyear}-{endyear}.nc"), use_cftime=True, preprocess=ose.preproc_pattern_2D)
    if ndim == '3D':
        pattern = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_pattern_{startyear}-{endyear}.nc"), use_cftime=True, preprocess=ose.preproc_pattern_3D)
    field = pattern.isel(time=0)*0

    for i in range(window):        
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_timeseries_{startyear}-{endyear}_0000{i}.nc")
        if ndim == '2D':
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=ose.preproc_timeseries_2D)        
        if ndim == '3D':
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=ose.preproc_timeseries_3D)        
        p = timeseries.polyfit(dim='time', deg=1, skipna = True)
        theta = xr.polyval(foredate, p[f"{var}_polyfit_coefficients"])
        laststep = pattern.isel(time=i)
        field = field + theta.isel(time=0,lat=0,lon=0)*laststep

    # save EOF
    ose.save_EOF(expname, startyear, endyear, field, var, ndim)

    # add trend
    ose.add_trend_EOF(expname, startyear, endyear, var)

    # read forecast and change restart
    data = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_forecast_{startyear}-{endyear}.nc"), use_cftime=True, preprocess=ose.preproc_forecast_3D) 
    rdata = osi.read_rebuilt(expname, endleg, endleg)
    data['time_counter'] = rdata['time_counter']
    varlist = ['tn', 'tb']
    for var1 in varlist:
        rdata[var1] = data[var]

    return rdata


def water_column_stabilizer(nc_file):
    """ stabilizer of temperature and salinity profiles  """    

    # Open the NetCDF file
    ds = xr.open_dataset(nc_file)
    
    # Extract temperature and salinity fields
    temperature = ds['temperature']
    salinity = ds['salinity']
    
    # create density field using the state equation: alpha*T+beta*S?
    rho = temperature + salinity

    # Calculate the vertical derivative of temperature and salinity
    dTdz = temperature.diff('depth') / temperature['depth'].diff('depth')
    dSdz = salinity.diff('depth') / salinity['depth'].diff('depth')
    
    # Define a threshold for instability (this is an example, you may need to adjust it)
    instability_threshold = 0  # Example threshold, needs to be defined appropriately
    
    # Identify unstable zones
    unstable_zones = (dTdz > instability_threshold)

    # Correct unstable zones by homogenizing temperature
    for i in range(temperature.shape[0] - 1):
        unstable_layer = unstable_zones.isel(depth=i)
        if unstable_layer.any():
            # Calculate mean temperature for the unstable layer
            temp_mean = (temperature.isel(depth=i) + temperature.isel(depth=i + 1)) / 2
            
            # Apply the mean temperature to the unstable layer
            temperature[i:i+2] = temp_mean
    
    # Update the dataset with the corrected temperature
    ds['temperature'] = temperature
    
    # Save the modified dataset to a new NetCDF file
    ds.to_netcdf('corrected_' + nc_file)
    
    # Close the dataset
    ds.close()

    return None