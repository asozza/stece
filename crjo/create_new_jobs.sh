#!/bin/bash

# before creating a new folder check paths in user-config.yml
# remember also that ini_dir is defined in /sources/se/ecmwf

# ./crjo.sh [OPTIONS]
# mandatory flags:
# --balancing / -b: namcouple, freq, time, 
# --production / -p: 
# optional flags:
# --copy-weights / -w: set true (otherwise is always false)
# --nemo-list-only / -l: set true in template/nemo/oce-... 
# arguments (mandatory): 
# --expname / -e: name of the experiment
# --kind <value> / -k (value=amip or cpld)
# --nproc / -n: 100,154
# 

while getopts 'lp:' OPTION; do
  case "$OPTION" in
    l)
      echo "load balancing"
      # modify the namcouple, freq & time, 
      ;;
    p)
      echo "production"        
      ;;
    a)
      avalue="$OPTARG"
      echo "The value provided is $OPTARG"
      ;;
    ?)
      echo "script usage: $(basename \$0) [-l] [-h] [-a somevalue]" >&2
      exit 1
      ;;
  esac
done
shift "$(($OPTIND -1))"

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
