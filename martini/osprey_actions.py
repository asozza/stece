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
import osprey_means as om


# action: rebuild
def rebuild_nemo(expname, leg, dirs):
    """Minimal nemo rebuilder in a temporary path"""

    dirs = io.folders(expname, leg)

    rebuilder = os.path.join(dirs['rebuild'], "rebuild_nemo")
  
    for kind in ['restart', 'restart_ice']:
        print('Processing' + kind)
        flist = glob.glob(os.path.join(dirs['exp'], 'restart', leg.zfill(3), expname + '*_' + kind + '_????.nc'))
        tstep = io.get_nemo_timestep(flist[0])

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], os.path.basename(filename))
            try:
                os.symlink(filename, destination_path)
            except FileExistsError:
                pass

        rebuild_command = [rebuilder, "-m", os.path.join(dirs['tmp'],  expname + "_" + tstep + "_" + kind ), str(len(flist))]
        try:
            subprocess.run(rebuild_command, stderr=subprocess.PIPE, text=True, check=True)
            for file in glob.glob('nam_rebuld_*') : 
                os.remove(file)
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            print(error_message) 

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], os.path.basename(filename))
            os.remove(destination_path)

    # read timestep
    filelist = glob.glob(os.path.join(dirs['tmp'],  expname + '*_restart.nc'))
    timestep = io.get_nemo_timestep(filelist[0])

    # copy restart
    shutil.copy(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart.nc'), os.path.join(dirs['tmp'], 'restart.nc'))
    shutil.copy(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart_ice.nc'), os.path.join(dirs['tmp'], 'restart_ice.nc'))

    # remove 
    os.remove(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart.nc'))
    os.remove(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart_ice.nc'))

    flist = glob.glob('nam_rebuild*')
    for file in flist:
        os.remove(file)


# action rollback
def rollback_ece4(expname, leg, dirs):
    
    # define directories
    dirs = io.folders(expname, leg)

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
    flist = glob.glob(os.path.join(dirs['exp'], 'restart', leg.zfill(3), expname + '*_' + 'restart' + '_????.nc'))
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
        filelist = sorted(glob.glob(os.path.join(dirs['exp'],  'restart', leg.zfill(3), file)))
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

    dirs = io.folders(expname, leg)

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
        rebfile = os.path.join(dirs['tmp'], file)
        resfile = os.path.join(dirs['exp'], 'restart', leg.zfill(3), file)
        shutil.copy(rebfile, resfile)
        newfile = os.path.join(dirs['exp'], file)
        print("Linking rebuilt NEMO restart", file)            
        os.symlink(resfile, newfile)


# action: forecast (diversify: constant, local, eof)
def forecast_T_ave(expname, leg, yearspan, yearleap):

    dirs = io.folders(expname, leg)
    df = om.elements(expname)

    # extrapolate future global temperature
    legfile = os.path.join(dirs['exp'], 'leginfo.yml')
    with open(legfile, 'r', encoding='utf-8') as file:
        leginfo = yaml.load(file, Loader=yaml.FullLoader)
    info = leginfo['base.context']['experiment']['schedule']['leg']
    endyear = info['start'].year - 1
    startyear = endyear - yearspan
    print('Fitting in the range: ',startyear,endyear)

    # read data
    data = io.readmf_T(expname, startyear, endyear)

    # extract averaged T filtered
    tt = data['time'].values.flatten()
    tom = om.moving_average(data['to'].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)

    # fit global temperature
    Yg = [[tom[i]] for i in range(len(tom))]
    Xg = [[tt[i]] for i in range(len(tt))]
    model=LinearRegression()
    model.fit(Xg, Yg)
    mp = model.coef_[0][0]
    qp = model.intercept_[0]
    teq = mp*(endyear+yearleap) + qp
    print(' Fit coefficients: ',mp,qp)
    print(' Projected Temperature: ',teq)

    return teq

# action: manipulate (diversify: constant, local, eof)
def manipulate(expname, leg):

    dirs = io.folders(expname, leg)

    # extract start and end years

    # read output fields in the time window
    data = io.readmf_T(expname, startyear, endyear)
    tf = len(data['time'])
    xt0 = data['to'].isel(time=0)
    xt1 = data['to'].isel(time=tf-1)
    xt0 = xt0.rename({'z': 'nav_lev'})
    xt1 = xt1.rename({'z': 'nav_lev'})

    # modify restart files
    domain = domain.rename({'z': 'nav_lev'})
    vol = domain['e1t']*domain['e2t']*domain['e3t_0']
    filelist = glob.glob(os.path.join(dirs['tmp'],  expname + '*_restart.nc'))
    timestep = io.get_nemo_timestep(filelist[0])
    oce = os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart.nc')
    xfield = xr.open_dataset(oce)
    varlist = ['tn', 'tb']
    for var in varlist:
        tef = xfield[var].where(xfield[var]!=0.0).isel(time_counter=0).weighted(vol).mean(dim=['nav_lev', 'y', 'x']).values
        print('Last value of Temperature: ',var,tef[0])
        trel = teq/tef[0]
        dxt = xr.where(xt0 > xt1, 1.0-trel, 1.0+trel)
        xfield[var] = xr.where(xfield[var]!=0, dxt*xfield[var], 0.0)

def manipulate(expname, leg):

    filelist = glob.glob(os.path.join(dirs['tmp'],  expname + '*_restart.nc'))
    timestep = io.get_nemo_timestep(filelist[0])
    oce = os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart.nc')
    xfield = xr.open_dataset(oce)
    varlist = ['tn', 'tb']
    for var in varlist:
        xfield[var] = xr.where(xfield[var]!=0, xfield[var] - 1.0, 0.)
    
    # ocean restart creation
    oceout = os.path.join(dirs['tmp'], 'restart.nc')
    xfield.to_netcdf(oceout)

    # ice restart copy
    shutil.copy(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart_ice.nc'), os.path.join(dirs['tmp'], 'restart_ice.nc'))

#
def write_nemo_restart(expname, xfield, leg):

    # get timestep
    dirs = io.folders(expname, leg)
    filelist = glob.glob(os.path.join(dirs['tmp'],  expname + '*_restart.nc'))
    timestep = io.get_nemo_timestep(filelist[0])
    
    # ocean restart creation
    oceout = os.path.join(dirs['tmp'], 'restart.nc')
    xfield.to_netcdf(oceout)

    # copy ice restart
    shutil.copy(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart_ice.nc'), os.path.join(dirs['tmp'], 'restart_ice.nc'))

