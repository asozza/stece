#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rebuilder

Authors: Paolo Davini, Alessandro Sozza (CNR-ISAC) 
Date: Oct 2023
"""

import subprocess
import os
import glob
import shutil

from osprey.utils import config
from osprey.utils.utils import get_nemo_timestep


def rebuilder(expname, leg):
    """Function to rebuild NEMO restart """

    dirs = config.folders(expname)
    
    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)

    rebuild_exe = os.path.join(dirs['rebuild'], "rebuild_nemo")
  
    for kind in ['restart', 'restart_ice']:
        print(' Processing ' + kind)
        flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + kind + '_????.nc'))
        tstep = get_nemo_timestep(flist[0])

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], str(leg).zfill(3), os.path.basename(filename))
            try:
                os.symlink(filename, destination_path)
            except FileExistsError:
                pass

        rebuild_command = [rebuild_exe, "-m", os.path.join(dirs['tmp'], str(leg).zfill(3), expname + "_" + tstep + "_" + kind ), str(len(flist))]
        try:
            subprocess.run(rebuild_command, stderr=subprocess.PIPE, text=True, check=True)
            for file in glob.glob('nam_rebuld_*'):
                os.remove(file)
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            print(error_message)

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], str(leg).zfill(3), os.path.basename(filename))
            os.remove(destination_path)

    # copy restart
    shutil.copy(os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart.nc'), os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart.nc'))
    shutil.copy(os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart_ice.nc'), os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart_ice.nc'))

    # delete temporary files
    flist = glob.glob('nam_rebuild*')
    for file in flist:
        os.remove(file)

