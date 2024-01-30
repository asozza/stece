#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a command line tool to modfy the NEMO restart files from a specific EC-Eart4
experiment, given a specific experiment and leg. 

Authors
Alessandro Sozza and Paolo Davini (CNR-ISAC, Nov 2023)
"""

import subprocess
import os
import glob
import shutil
import yaml
import argparse
import xarray as xr
from functions import preproc_nemo_T
from functions import dateDecimal

# on atos, you will need to have
# module load intel/2021.4.0 intel-mkl/19.0.5 prgenv/intel hdf5 netcdf4 
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/apps/netcdf4/4.9.1/INTEL/2021.4/lib:/usr/local/apps/hdf5/1.12.2/INTEL/2021.4/lib

def parse_args():
    """Command line parser for nemo-restart"""

    parser = argparse.ArgumentParser(description="Command Line Parser for nemo-restart")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("leg", metavar="LEG", help="The leg you want to process for rebuilding", type=str)
    parser.add_argument("yearspan", metavar="YEARSPAN", help="Year span for fitting global temperature", type=int)
    parser.add_argument("yearleap", metavar="YEARLEAP", help="Year leap for projecting global temperature", type=int)

    # optional to activate nemo rebuild
    parser.add_argument("--rebuild", action="store_true", help="Enable nemo-rebuild")
    parser.add_argument("--replace", action="store_true", help="Replace nemo restart files")


    parsed = parser.parse_args()

    return parsed

def get_nemo_timestep(filename):
    """Minimal function to get the timestep from a nemo restart file"""

    return os.path.basename(filename).split('_')[1]

def rebuild_nemo(expname, leg, dirs):
    """Minimal nemo rebuilder in a temporary path"""

    rebuilder = os.path.join(dirs['rebuild'], "rebuild_nemo")
  
    for kind in ['restart', 'restart_ice']:
        print('Processing' + kind)
        flist = glob.glob(os.path.join(dirs['exp'], 'restart', leg.zfill(3), expname + '*_' + kind + '_????.nc'))
        tstep = get_nemo_timestep(flist[0])

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], leg.zfill(3), os.path.basename(filename))
            try:
                os.symlink(filename, destination_path)
            except FileExistsError:
                pass

        rebuild_command = [rebuilder, os.path.join(dirs['tmp'], leg.zfill(3), expname + "_" + tstep + "_" + kind ), str(len(flist))]
        try:
            subprocess.run(rebuild_command, stderr=subprocess.PIPE, text=True, check=True)
            for file in glob.glob('nam_rebuld_*') : 
                os.remove(file)
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            print(error_message) 

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], leg.zfill(3), os.path.basename(filename))
            os.remove(destination_path)


if __name__ == "__main__":
    
    # parser
    args = parse_args()
    expname = args.expname
    leg = args.leg
    yearspan = args.yearspan
    yearleap = args.yearleap
    legstart = str(int(leg)-yearspan)

    # define directories
    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'nemo': os.path.join("/ec/res4/scratch/itas/ece4/", expname, "output", "nemo"),
        'restart': os.path.join("/ec/res4/scratch/itas/ece4/", expname, "output", "restart"),
        'tmp': os.path.join("/ec/res4/scratch/itas/martini", expname),
        'rebuild': "/ec/res4/hpcperm/itas/src/rebuild_nemo"
    }

    tmpleg = os.path.join(dirs['tmp'], leg.zfill(3))
    tmpleg0 = os.path.join(dirs['tmp'], legstart.zfill(3))

    os.makedirs(tmpleg, exist_ok=True)
    os.makedirs(tmpleg0, exist_ok=True)

    # rebuild nemo restart files
    if args.rebuild:
        rebuild_nemo(expname=expname, leg=leg, dirs=dirs)
        rebuild_nemo(expname=expname, leg=legstart, dirs=dirs)

    # extrapolate future global temperature
    legfile = os.path.join(dirs['exp'], 'leginfo.yml')
    with open(legfile, 'r', encoding='utf-8') as file:
        leginfo = yaml.load(file, Loader=yaml.FullLoader)
    info = leginfo['base.context']['experiment']['schedule']['leg']
    endyear = info['start'].year - 1
    startyear = endyear - yearspan
    print('Working in the range: ',startyear,endyear)

    # modify restart files
    flist = glob.glob(os.path.join(dirs['tmp'], legstart.zfill(3), expname + '*_restart.nc'))
    tstep = get_nemo_timestep(flist[0])
    oce = os.path.join(dirs['tmp'], legstart.zfill(3), expname + '_' + tstep + '_restart.nc')
    xfield0 = xr.open_dataset(oce)
    flist = glob.glob(os.path.join(dirs['tmp'], leg.zfill(3), expname + '*_restart.nc'))
    tstep = get_nemo_timestep(flist[0])
    oce = os.path.join(dirs['tmp'], leg.zfill(3), expname + '_' + tstep + '_restart.nc')
    xfield = xr.open_dataset(oce)

    varlist = ['tn', 'tb']
    for var in varlist:
        xt1 = xfield[var].values
        xt0 = xfield0[var].values
        #dxt = ((endyear+yearleap)*(xt1-xt0)+xt0*endyear-xt1*startyear)/(endyear-startyear)
        dxt = xt1+yearleap*(xt1-xt0)/(endyear-startyear)
        xfield[var] = xr.where(xfield[var]!=0, dxt, 0.0)
    
    #################################################################################

    # ocean restart creation
    oceout = os.path.join(dirs['tmp'], leg.zfill(3), 'restart.nc')
    xfield.to_netcdf(oceout)

    # ice restart copy
    shutil.copy(os.path.join(dirs['tmp'], leg.zfill(3), expname + '_' + tstep + '_restart_ice.nc'), os.path.join(dirs['tmp'], leg.zfill(3), 'restart_ice.nc'))

    # replace nemo restart files
    if args.replace:
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
            rebfile = os.path.join(dirs['tmp'], leg.zfill(3), file)
            resfile = os.path.join(dirs['exp'], 'restart', leg.zfill(3), file)
            shutil.copy(rebfile, resfile)
            newfile = os.path.join(dirs['exp'], file)
            print("Linking rebuilt NEMO restart", file)            
            os.symlink(resfile, newfile)

