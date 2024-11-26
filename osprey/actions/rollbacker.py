#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rollbacker

Author: Paolo Davini, Alessandro Sozza (CNR-ISAC) 
Date: Oct 2023
"""

import os
import re
import glob
import shutil
import yaml
from dateutil.relativedelta import relativedelta

from osprey.utils.folders import folders
from osprey.utils.utils import get_nemo_timestep
from osprey.utils.time import get_year

def rollbacker(expname, leg):
    """ Function to rollback an EC-Earth4 run to a previous leg """

    # Define directories
    dirs = folders(expname)
    year = get_year(leg)

    # Cleaning - remove files in the run folder
    files_to_remove = ['rstas.nc', 'rstos.nc', 'srf*', 'restart*.nc', 'rcf']
    for file_pattern in files_to_remove:
        filelist = sorted(glob.glob(os.path.join(dirs['exp'], file_pattern)))
        for file in filelist:
            if os.path.isfile(file):
                print(f'Removing {file}')
                os.remove(file)

    # Remove rebuilt restart files in the restart/$leg folder
    restart_files = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), 'restart*.nc'))
    for file in restart_files:
        if os.path.isfile(file):
            print(f'Removing {file}')
            os.remove(file)

    # Remove restart folders with leg > $leg
    folder_pattern = re.compile(r'^\d{3}$')
    for folder in ['restart', 'log']:
        for folder_name in os.listdir(dirs[folder]):
            folder_path = os.path.join(dirs[folder], folder_name)
            if os.path.isdir(folder_path) and folder_pattern.match(folder_name):
                folder_number = int(folder_name)
                if folder_number > (leg if folder == 'restart' else leg - 1):
                    print(f"Deleting folder: {folder_name}")
                    shutil.rmtree(folder_path)

    # Remove output files in nemo & oifs
    file_pattern = re.compile(r'_(\d{4})-(\d{4})\.nc$')
    components = ['nemo', 'oifs']
    for cname in components:
        for filename in os.listdir(dirs[cname]):
            file_path = os.path.join(dirs[cname], filename)
            match = file_pattern.search(filename)
            if match:
                start_year, end_year = int(match.group(1)), int(match.group(2))
                if end_year > year:
                    print(f"Deleting file: {filename}")
                    os.remove(file_path)

    # Update time.step
    restart_files = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), f"*_restart_*.nc"))
    if restart_files:
        timestep = get_nemo_timestep(restart_files[0])
        tstepfile = os.path.join(dirs['exp'], 'time.step')
        with open(tstepfile, 'w', encoding='utf-8') as file:
            file.write(str(int(timestep)))

    # Update leginfo.yml
    legfile = os.path.join(dirs['exp'], 'leginfo.yml')
    with open(legfile, 'r', encoding='utf-8') as file:
        leginfo = yaml.load(file, Loader=yaml.FullLoader)

    info = leginfo['base.context']['experiment']['schedule']['leg']
    deltaleg = int(leg) - info['num']    
    newdate = info['start'] + relativedelta(years=deltaleg)
    orgdate = info['start']

    # Modify leginfo.yml if necessary
    if int(leg) < info['num']:
        leginfo['base.context']['experiment']['schedule']['leg']['start'] = newdate
        leginfo['base.context']['experiment']['schedule']['leg']['num'] = int(leg)

        print(f"Updating leginfo to leg number {leg}")
        with open(legfile, 'w', encoding='utf8') as outfile:
            yaml.dump(leginfo, outfile, default_flow_style=False)
    elif int(leg) == info['num']:
        print("Nothing to do on leginfo.yml")
    else:
        raise ValueError("Cannot go forward in time.")

    # Copying restart files for the requested leg
    restart_patterns = ['rstas.nc', 'rstos.nc', 'srf*', 'rcf', '*restart*']
    for file_pattern in restart_patterns:
        filelist = sorted(glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), file_pattern)))
        for file in filelist:
            basefile = os.path.basename(file)
            targetfile = os.path.join(dirs['exp'], basefile)
            if not os.path.isfile(targetfile):
                if basefile in ['rstas.nc', 'rstos.nc', 'rcf']:
                    print(f"Copying restart {file}")
                    shutil.copy(file, targetfile)
                elif 'srf' in basefile:
                    print(f"Linking IFS restart {file}")
                    os.symlink(file, targetfile)
                elif 'restart' in basefile:
                    newfile = os.path.join(dirs['exp'], '_'.join(basefile.split('_')[2:]))
                    print(f"Linking NEMO restart {file}")
                    os.symlink(file, newfile)

    # Remove old output to avoid confusion
    for year in range(newdate.year, orgdate.year):
        filelist = sorted(glob.glob(os.path.join(dirs['exp'], 'output', '*', f'*{year}*')))
        for file in filelist:
            if os.path.isfile(file):
                print(f'Removing output file {file}')
                os.remove(file)

    return None
