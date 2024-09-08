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

# Set up logging (if not already set up)
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_bash_command(command):
    """Run a bash command using subprocess"""

    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Command executed: {command}")
        
        if result.stdout:
            logger.info(f"Command stdout: {result.stdout.decode('utf-8').strip()}")
        if result.stderr:
            logger.warning(f"Command stderr: {result.stderr.decode('utf-8').strip()}")
        return result.stdout.decode('utf-8').strip()

    except subprocess.CalledProcessError as e:        
        logger.error(f"Command '{command}' failed with return code {e.returncode}")
        logger.error(f"Error output: {e.stderr.decode('utf-8').strip()}")
        
        raise

def remove_existing_file(filename):

    try:
        os.remove(filename)
        logger.info(f"File {filename} successfully removed.")
    except FileNotFoundError:
        logger.info(f"File {filename} not found.")


def remove_existing_filelist(filename):

    pattern = os.path.join(filename + '*.nc')
    files = glob.glob(pattern)
    try:
        for file in files:
            os.remove(file)
            logger.info(f"File {file} successfully removed.")
    except FileNotFoundError:
        logger.error(f"File {file} not found.")


def error_handling_decorator(func):
    """Decorator to add standardized error handling to functions."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as fnf_error:
            logger.error(f"File not found: {fnf_error}")
        except PermissionError as perm_error:
            logger.error(f"Permission denied: {perm_error}")
        except ValueError as val_error:
            logger.error(f"Value error: {val_error}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        else:
            logger.info(f"Function {func.__name__} completed successfully.")
        finally:
            logger.info(f"Execution of {func.__name__} finished.")
    
    return wrapper

def get_expname(data):
    """" Get expname from a NEMO dataset & output file path """

    return os.path.basename(data.attrs['name']).split('_')[0]


def get_nemo_timestep(filename):
    """ Get timestep from a NEMO restart file """

    return os.path.basename(filename).split('_')[1]

