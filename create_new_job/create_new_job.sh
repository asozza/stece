#!/bin/bash

# before creating a new folder check paths in user-config.yml
# remember also that ini_dir is defined in /sources/se/ecmwf

jobname=$1
kind=$2
machine=ecmwf-hpc2020-intel+openmpi

if [ -z $jobname ] ; then
	echo " usage ./create_new_job.sh jobname kind ('amip' or 'cpld') "
	exit 1
fi

if [ -z $kind ] ; then
        echo " usage ./create_new_job.sh jobname kind ('amip' or 'cpld') "
        exit 1
fi

mkdir -p $jobname
cp -r defaults/scriptlib $jobname
cp -r defaults/templates $jobname
cp defaults/experiment-config-$kind.yml $jobname/$jobname.yml
sed -i "s/TEST/${jobname}/g" $jobname/$jobname.yml
cp defaults/user-config.yml $jobname
cp defaults/launch.sh $jobname
sed -i "s/TEST/${jobname}/g" $jobname/launch.sh
