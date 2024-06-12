#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Replacer

Author: Alessandro Sozza (CNR-ISAC)
Date: Oct 2023
"""

import os
import glob
import shutil

from osprey.reader.reader import folders


def replacer(expname, leg):
    """ Function to replace modified restart files in the run folder """

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

