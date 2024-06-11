#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilities module

Author: Alessandro Sozza (CNR-ISAC) 
Date: May 2024
"""

import os
import subprocess

def run_bash_command(command):
    """ Run a bash command using subprocess """

    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode('utf-8'))
        print(result.stderr.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with return code {e.returncode}")
        print(e.output.decode('utf-8'))
        print(e.stderr.decode('utf-8'))
        raise


def get_expname(data):
    """" Get expname from a NEMO dataset & output file path """

    return os.path.basename(data.attrs['name']).split('_')[0]


def get_nemo_timestep(filename):
    """ Get timestep from a NEMO restart file """

    return os.path.basename(filename).split('_')[1]

def flatten_to_triad(m, nj, ni):
    """ Recover triad indexes from flatten array length """

    k = m // (ni * nj)
    j = (m - k * ni * nj) // ni
    i = m - k * ni * nj - j * ni

    return k, j, i
