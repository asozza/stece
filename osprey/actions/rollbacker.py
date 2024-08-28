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

from osprey.actions.reader import folders
from osprey.utils.utils import get_nemo_timestep


def rollbacker(expname, leg):
    """ Function to rollback ECE4 run to a previous leg """

    # define directories
    dirs = folders(expname)

    # cleaning
    # create list of files to be removed in the run folder
    browser = ['rstas.nc', 'rstos.nc',  'srf000*.????', 'restart*.nc', 'rcf']
    for file in browser:
        filelist = sorted(glob.glob(os.path.join(dirs['exp'], file)))
        for file in filelist:
            if os.path.isfile(file):
                print('Removing' + file)
                os.remove(file)

    # remove also rebuilt restart in the restart/$leg folder
    filelist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), 'restart*.nc'))
    for file in filelist:
        if os.path.isfile(file):
            print('Removing' + file)
            os.remove(file)

    # remove folders with leg > $leg
    folder_pattern = re.compile(r'^\d{3}$')
    # Iterate over all items in the directory
    for folder_name in os.listdir(dirs['restart']):
        folder_path = os.path.join(dirs['restart'], folder_name)
        # Check if it's a folder and if its name matches the three-digit pattern
        if os.path.isdir(folder_path) and folder_pattern.match(folder_name):
            folder_number = int(folder_name)
            # Delete the folder if its number is greater than the threshold
            if folder_number > leg:
                print(f"Deleting folder: {folder_name}")
                shutil.rmtree(folder_path)

    # update time.step
    flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + 'restart' + '_????.nc'))
    timestep = get_nemo_timestep(flist[0])
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
