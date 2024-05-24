#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Osprey library for actions

Authors
Alessandro Sozza (CNR-ISAC, Mar 2024)
"""

import subprocess
import numpy as np
import os
import glob
import shutil
import yaml
import argparse
import random
import xarray as xr
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from sklearn.linear_model import LinearRegression
import osprey_io as io
import osprey_means as osm


# action: rebuild
def rebuild_nemo(expname, leg):
    """ Minimal nemo rebuilder in a temporary path """

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
    
    #timestep = io.get_nemo_timestep(filelist[0])

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
    """ Rollback ECE4 run to a previous leg """

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
    """ Replace NEMO rebuilt field in the run folder """

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


# forecasting action
def forecast_T_ave(expname, leg, yearspan, yearleap):
    """ Forecast for T grid using global mean """

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
    print(' Projected Temperature: ',yf)

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
    """ Forecast for T grid using relative change based on global mean """

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
    print(' Projected Temperature: ',yf)

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
    """ Forecast for T grid using interpolation """

    startyear, endyear = io.start_end_years(expname, yearspan, leg)    
    rdata = io.read_restart(expname, leg)
    leg0 = int(leg)-int(yearspan)    
    rdata0 = io.read_restart(expname, leg0)

    varlist = ['tn', 'tb']
    for var in varlist:
        dxt = rdata[var].values+yearleap*(rdata[var].values-rdata0[var].values)/(endyear-startyear)
        rdata[var] = xr.where(rdata[var]!=0, dxt, 0.0)

    return rdata

def forecast_T_local_fit(expname, leg, yearspan, yearleap):
    """ Forecast for T grid using local fit """

    print(' loading data .... ')

    # load data
    endyear = 1990+int(leg)-2
    startyear = endyear - yearspan
    xf = endyear+yearleap
    data = io.readmf_T(expname, startyear, endyear)
    x = osm.dateDecimal(data['time'].values.flatten())

    print(' flattening and reshapening .... ')

    # flattened arrays
    ds = data['to'].isel(time=0)
    ds_flat = ds.values.flatten()
    to_flat = data['to'].values.flatten()

    to_reshaped = to_flat.reshape(len(x),-1)
    indices = ~np.isnan(to_reshaped)
    indices_flat = ~np.isnan(to_flat)
    to_valid = to_flat[indices_flat]
    size_valid = to_valid.shape[0]/len(x)
    to_wonan = np.zeros((len(x), int(size_valid)))
    to_wonan = to_reshaped[:, indices[0]]

    # fit and predict

    print(' forecasting .... ')

    to_pred = []
    model = LinearRegression()
    for i in range(to_wonan.shape[1]):
        #x_row = x_wonan[:, i].reshape(len(x),-1)
        x_row = np.array(x).reshape(len(x),-1)
        y_row = to_wonan[:, i].reshape(len(x),-1)
        model.fit(x_row, y_row)
        yf = model.predict([[xf]])
        to_pred.append(yf[0][0])

    print(' countercheck T<-2deg .... ')

    # check T < -2 deg
    y_last = []
    for i in range(to_wonan.shape[1]):
        y_last.append(to_wonan[-1, i])
    k=0
    for i in range(len(to_pred)):
        if to_pred[i] < -1.8:
            to_pred[i] = y_last[i]
            k += 1
    print(' Fraction of points below -2deg = ',k/len(to_pred))

    check_fit=True
    if check_fit:
        i=random.randint(0, to_wonan.shape[1]-1)
        kji = osm.flatten_to_triad(i, 31, 148, 180)
        model = LinearRegression()
        x_row = np.array(x).reshape(len(x),-1)
        y_row = to_wonan[:,i].reshape(len(x),-1)
        model.fit(x_row, y_row)
        mp = model.coef_[0][0]
        qp = model.intercept_[0]
        yf = model.predict([[xf]])
        ym = osm.movave(y_row.flatten(),12).reshape(len(x),-1)
        yp = []; xp = []
        for i in range(len(x)*2):
            xp.append(startyear+i/12.)
            yp.append(mp*(startyear+i/12.)+qp)
        plt.plot(x_row,y_row)
        plt.plot(x,ym)
        plt.plot(xp,yp)
        plt.scatter(xf,yf, color='green')
        plt.ylabel('temperature')
        plt.xlabel('time')
        plt.title('')
        plt.title(' (k,j,i) = {}'.format(kji))
        plt.gca().legend(('local trend','moving average','fit','projected value'))

    # fill new field
    theta = []
    j = 0
    for i in range(len(ds_flat)):
        if indices[0][i]:
            theta.append(to_pred[j])
            j += 1
        else:
            theta.append(np.nan)

    # reshape    
    te = np.array(theta).reshape((len(ds['z']),len(ds['y']),len(ds['x'])))
    
    # create new restart field using the forecast
    rdata = io.read_restart(expname, leg)
    varlist = ['tn', 'tb']
    for var in varlist:
        rdata[var] = xr.where(rdata[var]!=0.0, te, 0.0)

    return rdata

# manipulation using EOF
def forecast_T_EOF(expname, leg, yearspan, yearleap):
    """ Forecast for T grid using EOF """

    endyear = 1990+int(leg)-2
    startyear = endyear-yearspan
    foreyear = endyear+yearleap

    dirs = io.folders(expname)
    fldlist = []
    for year in range(startyear, endyear):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        fldlist.extend(matching_files)

    var='thetao'
    fldcat = os.path.join(dirs['tmp'], f"{expname}_{startyear}-{endyear}")
    fld = os.path.join(dirs['tmp'], f"{var}_{startyear}-{endyear}")
    flda = os.path.join(dirs['tmp'], f"{var}_anomaly_{startyear}-{endyear}")
    fldcov = os.path.join(dirs['tmp'], f"{var}_variance_{startyear}-{endyear}")
    fldpat = os.path.join(dirs['tmp'], f"{var}_pattern_{startyear}-{endyear}")
    timeseries = os.path.join(dirs['tmp'], f"{var}_timeseries_{startyear}-{endyear}")

    io.run_cdo(f"cdo cat {fldlist} {fldcat}")
    io.run_cdo(f"cdo yearmean -selname,{var} {fldcat} {fld}")
    io.run_cdo(f"cdo sub {fld} -timmean {fld} {flda}")
    io.run_cdo(f"cdo eof,10 {flda} {fldcov} {fldpat}")
    io.run_cdo(f"cdo eofcoeff {fldpat} {flda} {timeseries}")

    return rdata
# 

