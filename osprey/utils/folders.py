#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Folder definitions

Author: Alessandro Sozza (CNR-ISAC)
Date: Mar 2024
"""

import os

def folders(expname):
    """ List of global paths """

    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'nemo': os.path.join("/ec/res4/scratch/itas/ece4", expname, "output", "nemo"),
        'restart': os.path.join("/ec/res4/scratch/itas/ece4", expname, "restart"),
        'backup': os.path.join("/ec/res4/scratch/itas/ece4", expname + "-backup"),
        'tmp':  os.path.join("/ec/res4/scratch/itas/martini", expname),
        'rebuild': "/ec/res4/hpcperm/itas/src/rebuild_nemo",
        'perm': os.path.join("/perm/itas/ece4", expname, "nemo"),
        'eof': os.path.join("/ec/res4/scratch/itas/eof", expname)
    }

    return dirs