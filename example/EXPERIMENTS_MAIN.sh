#!/bin/bash

# include config and some utils
source $(ccc file_cfg)   # for envs in user provided .ccc_config.sh or .slurm_config.sh
source $(ccc file_utils) # for wait_or_interrupt in utils.sh

DO_TRAINING=True      # step 1: training
DO_EVALUATION=True    # step 2: evaluate

# additional info for SLURM jobs
export SLURM_JOB_ARGS=--output=logs/%j-node-%t.out --time=12:00:00 --mem-per-gpu=8G --partition=gpu --cpus-per-task=16 --exclude=gn01

# assuming 4 GPUs available on localhost
GPUS_FILE=$(ccc gpus --on_cluster=$(dirname $0)/cluster_info.json --gpus=2 --tasks=4 --hosts="HOST_A,HOST_B" --ignore_hosts="HOST_C")

########################################
# Training 
########################################

if [[ "$DO_TRAINING" == True ]] ; then

  for db in "vicos_towel"; do
    export CCC_DATASET=$db
    for backbone in "tu-convnext_base" "tu-convnext_large" ; do
      for epoch in 10; do
        for depth in off on; do 
          if [[ "$depth" == off ]] ; then
            export CCC_USE_DEPTH=False
          elif [[ "$depth" == on ]] ; then
            export CCC_USE_DEPTH=True 
          fi
          ccc run $GPUS_FILE python dummy.py --config dummy=True backbone=$backbone epoch=$epoch &
        done
      done
    done
  done
fi
wait_or_interrupt


########################################
# Evaluating on test data
########################################

if [[ "$DO_EVALUATION" == True ]] ; then

  for db in "vicos_towel"; do
    export CCC_DATASET=$db
    for backbone in "tu-convnext_base" "tu-convnext_large" ; do
      for epoch_train in 10; do
        for epoch_eval in 5 10; do
          for depth in off on; do
            if [[ "$depth" == off ]] ; then
              export CCC_USE_DEPTH=False
            elif [[ "$depth" == on ]] ; then
              export CCC_USE_DEPTH=True
            fi
            # run center model pre-trained on weakly-supervised
            ccc run $GPUS_FILE python dummy.py --config dummy=True backbone=$backbone epoch_train=$epoch_train epoch_eval=$epoch_eval &
          done
        done
      done
    done
  done
fi

wait_or_interrupt

rm $GPUS_FILE