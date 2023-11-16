#!/bin/bash

# before creating a new folder check paths in user-config.yml
# remember also that ini_dir is defined in /sources/se/ecmwf

jobname=$1
kind=$2
machine=ecmwf-hpc2020-intel+openmpi

ecedir=/ec/hpcperm/itmn/src/ecearth4-epochal
default=$ecedir/runtime/se
rundir=/ec/res4/scratch/itas/ece4
inidir=/ec/res4/hpcperm/itas/data/v4-trunk


if [ -z $jobname ] ; then
	echo " usage ./create_new_job.sh jobname kind ('amip' or 'cpld') "
	exit 1
fi

if [ -z $kind ] ; then
        echo " usage ./create_new_job.sh jobname kind ('amip' or 'cpld') "
        exit 1
fi

mkdir -p $jobname
cp -r $default/scriptlib $jobname
cp -r $default/templates $jobname

cp $default/experiment-config-$kind.yml $jobname/$jobname.yml
sed -i "s/TEST/${jobname}/g" $jobname/$jobname.yml

cp $default/user-config.yml $jobname
sed -i "s@RUNDIR@${rundir}@g" $jobname/user-config.yml
sed -i "s@BASEDIR@${ecedir}@g" $jobname/user-config.yml
sed -i "s@INIDIR@${inidir}@g" $jobname/user-config.yml

cp $default/launch.sh $jobname
sed -i "s@TEST@${jobname}@g" $jobname/launch.sh
sed -i "s@BASEDIR@${ecedir}@g" $jobname/launch.sh
