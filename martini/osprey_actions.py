#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 _____  __________  ____  ______   __ 
/  __ \/   __   _ \|  _ \|  ___ \ / / 
| |  |    |_ | |_|   |_|   |__ \ V /  
| |  | |\_  \|  __/|    /|  __| | |   
| |__| |__|    |   | |\ \| |____| |   
\___________/|_|   |_| \__________|   

OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Osprey library for actions

Authors
Alessandro Sozza (CNR-ISAC, Mar 2024)
"""

import subprocess
import os
import glob
import shutil
import yaml
import argparse
import xarray as xr
from dateutil.relativedelta import relativedelta
from sklearn.linear_model import LinearRegression
import osprey_io as io
import osprey_means as osm


# action: rebuild
def rebuild_nemo(expname, leg):
    """Minimal nemo rebuilder in a temporary path"""

    dirs = io.folders(expname)
    
    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)

    rebuilder = os.path.join(dirs['rebuild'], "rebuild_nemo")
  
    for kind in ['restart', 'restart_ice']:
        print(' Processing ' + kind)
        flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + kind + '_????.nc'))
        tstep = io.get_nemo_timestep(flist[0])

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
    filelist = glob.glob(os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart.nc'))
    timestep = io.get_nemo_timestep(filelist[0])

    # copy restart
    #shutil.copy(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart.nc'), os.path.join(dirs['tmp'], 'restart.nc'))
    #shutil.copy(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart_ice.nc'), os.path.join(dirs['tmp'], 'restart_ice.nc'))

    # remove 
    #os.remove(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart.nc'))
    #os.remove(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart_ice.nc'))

    flist = glob.glob('nam_rebuild*')
    for file in flist:
        os.remove(file)


# action rollback
def rollback_ece4(expname, leg):
    
    # define directories
    dirs = io.folders(expname)

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
    timestep = io.get_nemo_timestep(flist[0])
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


# action: replace 
def replace_nemo(expname, leg):

    dirs = io.folders(expname)

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


# action: forecast (diversify: constant, local, eof)
def forecast_T_ave(expname, leg, yearspan, yearleap):

    # load data
    df = osm.elements(expname)
    startyear, endyear = io.start_end_years(expname, yearspan, leg)
    data = io.readmf_T(expname, startyear, endyear)

    # averaged variables
    x = osm.dateDecimal(data['time'].values.flatten())
    y = osm.movave(data['to'].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)

    # fit / forecast
    xf = endyear + yearleap
    mp,qp = osm.linear_fit(x, y)
    yf = mp*xf + qp

    # create new restart field using forecast
    df['vol'] = df['vol'].rename({'z': 'nav_lev'})
    rdata = io.read_restart(expname, leg)
    varlist = ['tn', 'tb']
    for var in varlist:
        tef = rdata[var].where(rdata[var]!=0.0).isel(time_counter=0).weighted(df['vol']).mean(dim=['nav_lev', 'y', 'x']).values
        rdata[var] = xr.where(rdata[var]!=0.0, rdata[var] - tef[0] + yf, 0.0)

    return rdata

# relative change based on the global temperature
def forecast_T_rel(expname, leg, yearspan, yearleap):

    # load data
    df = osm.elements(expname)
    startyear, endyear = io.start_end_years(expname, yearspan, leg)
    data = io.readmf_T(expname, startyear, endyear)

    # averaged variables
    x = osm.dateDecimal(data['time'].values.flatten())
    y = osm.movave(data['to'].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)

    # fit / forecast
    xf = endyear+yearleap
    mp,qp = osm.linear_fit(x, y)
    yf = mp*xf + qp

    # create new restart field using forecast
    rdata = io.read_restart(expname, leg)
    leg0 = int(leg)-int(yearspan)
    rdata0 = io.read_restart(expname, leg0)
    df['vol'] = df['vol'].rename({'z': 'nav_lev'})
    varlist = ['tn', 'tb']
    for var in varlist:
        tef = rdata[var].where(rdata[var]!=0.0).isel(time_counter=0).weighted(df['vol']).mean(dim=['nav_lev', 'y', 'x']).values
        trel = abs(yf-tef[0])/yf
        delta = xr.where(rdata[var]!=0, rdata[var].values-rdata0[var].values, 0.0)
        rdata[var] = xr.where(delta>0, (1+trel)*rdata[var], (1-trel)*rdata[var])

    return rdata

#
def forecast_T_interp(expname, leg, yearspan, yearleap):

    startyear, endyear = io.start_end_years(expname, yearspan, leg)    
    rdata = io.read_restart(expname, leg)
    leg0 = int(leg)-int(yearspan)    
    rdata0 = io.read_restart(expname, leg0)

    varlist = ['tn', 'tb']
    for var in varlist:
        dxt = rdata[var].values+yearleap*(rdata[var].values-rdata0[var].values)/(endyear-startyear)
        rdata[var] = xr.where(rdata[var]!=0, dxt, 0.0)

    return rdata

# manipulate restart adding a constant (with sign)
# check what happens for T<4, and add a threshold
def manipulate_add_const(expname, leg, const):

    rdata = io.read_restart(expname, leg)
    varlist = ['tn', 'tb']
    for var in varlist:
        rdata[var] = xr.where(rdata[var]!=0, rdata[var] + const, 0.)

    return rdata
