#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fit the last chunk (qt vs to) and apply the new temperature to the restart ('tn' and 'tb')

Authors
Alessandro Sozza (CNR-ISAC, Nov 2023)
"""

import subprocess
import os
import glob
import shutil
import argparse
import yaml
import xarray as xr
from dateutil.relativedelta import relativedelta
from functions import preproc_nemo
from functions import linear_fit

def parse_args():
    """Command line parser for restart-by-chunks"""

    parser = argparse.ArgumentParser(description="Command Line Parser for restart-by-chunks")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("yearspan", metavar="YEARSPAN", help="Year span", type=str)
    
    # optional to activate nemo rebuild
    parser.add_argument("--rebuild", action="store_true", help="Enable nemo-rebuild")

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
            destination_path = os.path.join(dirs['tmp'], os.path.basename(filename))
            try:
                os.symlink(filename, destination_path)
            except FileExistsError:
                pass

        rebuild_command = [rebuilder, os.path.join(dirs['tmp'],  expname + "_" + tstep + "_" + kind ), str(len(flist))]
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


if __name__ == "__main__":
    
    # parser
    args = parse_args()
    expname = args.expname    
    yearspan = args.yearspan

     # define directories
    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'nemo': os.path.join('/ec/res4/scratch/itas/ece4/', expname, 'output', 'nemo')
        'rebuild': "/ec/res4/hpcperm/itas/src/rebuild_nemo"
    }

    # open legfile and read the last leg
    legfile = os.path.join(dirs['exp'], 'leginfo.yml')
    with open(legfile, 'r', encoding='utf-8') as file:
        leginfo = yaml.load(file, Loader=yaml.FullLoader)
    info = leginfo['base.context']['experiment']['schedule']['leg']

    # load output folder
    dirs['tmp'] = os.path.join("/ec/res4/scratch/itas/martini", expname, leg.zfill(3))
    os.makedirs(dirs['tmp'], exist_ok=True)

    # load domain
    domain = xr.open_dataset(os.path.join(nemo, '..', '..', 'domain_cfg.nc'))
    vol = domain['e1t']*domain['e2t']*domain['e3t_0']
    area = domain['e1t']*domain['e2t']

    # open database of the last chunk alone
    end_year = info['start']
    start_year = end_year - relativedelta(years=yearspan)
    filelist = []
    for year in range(start_year, end_year + 1):
        pattern = os.path.join(nemo, f"{expname}_oce_1m_T_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo)
    
    # extract variables (T,Q) filtered
    toa = data['to'].weighted(vol).mean(dim=['z', 'y', 'x']).values.flatten()
    qta = data['qt_oce'].weighted(area).mean(dim=['y', 'x']).values.flatten()
    
    # fit
    mp,qp = linear_fit(toa, qta)

    nf=len(toa)
    
    # this can be apply also locally
    mm = (qta[nf]-qta[0])/(toa[nf]-toa[0])
    qq = qta[nf]-mm*toa[nf]
    teq = toa[nf]-qta[nf]/mm # -qq/mm

    for i in range(len(x)):
        for j in range(len(y)):
            data['to'][i][j] = 
    
    data['thetao'] = xr.where(xfield[var]!=0, xfield[var] - 1.0, 0.)

    data['to'] = 

    # rebuild nemo

    # apply new temperature to tb and tn