#!/bin/bash

# before creating a new folder check paths in user-config.yml
# remember also that ini_dir is defined in /sources/se/ecmwf

jobname=$1
kind=$2
machine=ecmwf-hpc2020-intel+openmpi

ecedir=/ec/res4/hpcperm/itmn/src/ecearth4-epochal
default=$ecedir/runtime/se
expdir=/ec/res4/hpcperm/itmn/jobs
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

mkdir -p $expdir/$jobname
cp -r $default/scriptlib $expdir/$jobname
cp -r $default/templates $expdir/$jobname

cp $default/experiment-config-$kind.yml $expdir/$jobname/$jobname.yml
sed -i "s/TEST/${jobname}/g" $expdir/$jobname/$jobname.yml

cp $default/user-config.yml $expdir/$jobname
sed -i "s@RUNDIR@${rundir}@g" $expdir/$jobname/user-config.yml
sed -i "s@BASEDIR@${ecedir}@g" $expdir/$jobname/user-config.yml
sed -i "s@INIDIR@${inidir}@g" $expdir/$jobname/user-config.yml

cp $default/launch.sh $expdir/$jobname
sed -i "s@TEST@${jobname}@g" $expdir/$jobname/launch.sh
sed -i "s@BASEDIR@${ecedir}@g" $expdir/$jobname/launch.sh
