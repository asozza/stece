#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
roll back restart for EC-Earth3
If you want to restore the model to a specific date, just run this tool
"""

import argparse
import os
import yaml
import shutil
from dateutil.relativedelta import relativedelta
import glob

def parse_args():
    """Command line parser for nemo-restart"""

    parser = argparse.ArgumentParser(description="Command Line Parser for nemo-restart")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("leg", metavar="LEG", help="The leg you want roll back", type=str)

    # optional to activate nemo rebuild
    parser.add_argument("--rerun", action="store_true", help="Restore the a backup of the leginfo")
    parser.add_argument("--backup", action="store_true", help="Before running, create a backup of the entire folder. It might be slow!")


    parsed = parser.parse_args()

    return parsed

if __name__ == "__main__":
    
    # parser
    args = parse_args()
    expname = args.expname
    leg = args.leg
    rerun = args.rerun

    # define directories
    dirs = {
        'exp': os.path.join("/ec/res4/scratch/ccpd/ece4", expname)
    }

    if args.backup:
        print('Creating a backup, it can be VERY LONG...')
        shutil.copytree(dirs['exp'], dirs['exp']+'-backup', symlinks=True)

    # cleaning
    # create list of files
    browser = ['rstas.nc', 'rstos.nc',  'srf000*.????', 'restart*.nc', 'rcf']
    for file in browser: 
        filelist = sorted(glob.glob(os.path.join(dirs['exp'], file)))
        for file in filelist:
            if os.path.isfile(file):
                print('Removing' + file)
                os.remove(file)

    # update the leginfo
    legfile = os.path.join(dirs['exp'], 'leginfo.yml')
    backup = os.path.join(dirs['exp'], 'leginfo.yml.backup')
    if os.path.isfile(backup) and rerun:
        shutil.copy(backup, legfile)
    with open(legfile, 'r', encoding='utf-8') as file:
        leginfo = yaml.load(file, Loader=yaml.FullLoader)

    # get some time information
    info = leginfo['base.context']['experiment']['schedule']['leg']
    deltayear = int(leg) - info['num']
    newdate = info['start'] + relativedelta(years=deltayear)
    orgdate = info['start']

    # modify the file only if it is necessary
    if int(leg) < info['num']:

        # create a backup
        shutil.copy(legfile, backup)
        #print(info['start'] + relativedelta(years=deltayear))

        leginfo['base.context']['experiment']['schedule']['leg']['num'] = int(leg)
        leginfo['base.context']['experiment']['schedule']['leg']['start'] = newdate

        print("Updating the leginfo to leg number " + leg)
        with open(legfile, 'w') as outfile:
            yaml.dump(leginfo, outfile, default_flow_style=False)
    
    elif int(leg) == info['num']:
        print("Nothing to do on the leginfo.yaml")
    else:
        raise ValueError("I cannot go forward in time...")
    
    # copying old restart 
    browser = ['rstas.nc', 'rstos.nc',  'srf000*.????', expname + '_restart*.nc', 'rcf']
    for file in browser: 
        filelist = sorted(glob.glob(os.path.join(dirs['exp'],  'restart', leg.zfill(3), file)))
        for file in filelist:
            targetfile = os.path.join(dirs['exp'], os.path.basename(file))
            if not os.path.isfile(targetfile):
                print("Copying restart", file)
                if os.path.basename(file) is ['rstas.nc', 'rstos.nc', 'rcf']:
                    shutil.copy(file, targetfile)
                else:
                    os.symlink(file, targetfile)

    # removing old output: this is irreversible
    browser = list(range(newdate.year, orgdate.year))
    for year in browser:
        filelist = sorted(glob.glob(os.path.join(dirs['exp'],  'output', '*', '*' + str(year) + '*')))
        for file in filelist: 
            if os.path.isfile(file):
                print('Removing output file', file)
                os.remove(file)

    


    



