#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilities module

Author: Alessandro Sozza (CNR-ISAC) 
Date: May 2024
"""

import os
import glob
import subprocess
import logging

def run_bash_command(command):
    """ Run a bash command using subprocess """

    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Command: '{command}' ")
        print(result.stdout.decode('utf-8'))
        print(result.stderr.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with return code {e.returncode}")
        print(e.output.decode('utf-8'))
        print(e.stderr.decode('utf-8'))
        raise


def remove_existing_file(filename):

    try:
        os.remove(filename)
        print(f"File {filename} successfully removed.")
    except FileNotFoundError:
        print(f"File {filename} not found.")

def remove_existing_filelist(filename):

    pattern = os.path.join(filename, '*.nc')
    files = glob.glob(pattern)
    try:
        for file in files:
            os.remove(file)
            print(f"File {file} successfully removed.")
    except FileNotFoundError:
        print(f"File {file} not found.")

def get_expname(data):
    """" Get expname from a NEMO dataset & output file path """

    return os.path.basename(data.attrs['name']).split('_')[0]


def get_nemo_timestep(filename):
    """ Get timestep from a NEMO restart file """

    return os.path.basename(filename).split('_')[1]

