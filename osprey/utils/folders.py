#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Folder definitions

Author: Alessandro Sozza (CNR-ISAC)
Date: Mar 2024
"""

import os

def folders(expname):
    """ List of global paths dependent on expname """

    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'nemo': os.path.join("/ec/res4/scratch/itas/ece4", expname, "output", "nemo"),
        'oifs': os.path.join("/ec/res4/scratch/itas/ece4", expname, "output", "oifs"),
        'restart': os.path.join("/ec/res4/scratch/itas/ece4", expname, "restart"),
        'log': os.path.join("/ec/res4/scratch/itas/ece4", expname, "log"),        
        'tmp':  os.path.join("/ec/res4/scratch/itas/martini", expname),
        'rebuild': "/ec/res4/hpcperm/itas/src/rebuild_nemo",
        'post': os.path.join("/ec/res4/scratch/itas/ece4", expname, "post"),
        'perm': os.path.join("/perm/itas/ece4", expname, "nemo")
    }

    return dirs

def paths():
    """ List of global paths """

    dirs = {
        'rebuild': "/ec/res4/hpcperm/itas/src/rebuild_nemo",
        'osprey': "/ec/res4/hpcperm/itas/src/github/stece/osprey/figs",
        'domain': "/ec/res4/hpcperm/itas/data/ECE4-DATA/nemo/domain"
    }

    return dirs