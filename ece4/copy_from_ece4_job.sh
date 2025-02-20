#!/bin/bash

# BASIC TOOL TO CREATE A NEW JOB FROM AN OLDER ONE CHANGING THE EXPID

# please define where the jobs are
expdir=$HPCPERM/ecearth4/jobs

exp1=$1
exp2=$2

if [ -z $exp1 ] ; then
	echo " usage ./copy_from_ece4_job.sh job1 job2 "
	exit 1
fi

if [ -z $exp2 ] ; then
        echo " usage ./copy_from_ece4_job.sh job1 job2 "
        exit 1
fi

cp -r $expdir/$exp1 $expdir/$exp2

rm -f $expdir/$exp2/${exp1}.log
mv $expdir/$exp2/${exp1}.yml $expdir/$exp2/${exp2}.yml

# expid is the third line, if this changes it will no longer work
sed -i "3,$ s/${exp1}/${exp2}/g" $expdir/$exp2/${exp2}.yml
sed -i "s/${exp1}/${exp2}/g" $expdir/$exp2/launch.sh

rm -rf $expdir/$exp2/ecs*
rm -rf $expdir/$exp2/*~
rm -rf $expdir/$exp2/sbatch.tmp.yml
