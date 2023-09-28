#!/bin/bash

# basic script to run the ECE4 job

expname=TEST
ECEDIR=/ec/res4/hpcperm/itas/src/gitlab/ecearth4
SRCDIR=$ECEDIR/sources/se
platform=ecmwf-hpc2020-intel+openmpi

se $SRCDIR/platforms/$platform.yml ${expname}.yml user-config.yml scriptlib/main.yml --loglevel debug
