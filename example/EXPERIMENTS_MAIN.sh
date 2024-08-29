#!/bin/bash

# include config and some utils
source $(ccc file_cfg)   # for envs in user provided .ccc_config.sh
source $(ccc file_utils) # for wait_or_interrupt in utils.sh

DO_TRAINING=True      # step 1: training
DO_EVALUATION=True    # step 2: evaluate

mapfile -t GPU_LIST < <(ccc gpus --on_cluster=$(dirname $0)/cluster_info.json --gpus=1 --tasks=4 --hosts="HOST_A,HOST_B" --ignore_hosts="HOST_C")
GPU_COUNT=${#GPU_LIST[@]}

########################################
# Training 
########################################

if [[ "$DO_TRAINING" == True ]] ; then
  s=0

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
          SERVERS=${GPU_LIST[$((s % GPU_COUNT))]} ccc run python dummy.py --config dummy=True backbone=$backbone epoch=$epoch &
          s=$((s+1))
          wait_or_interrupt $GPU_COUNT $s
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
  s=0

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
            SERVERS=${GPU_LIST[$((s % GPU_COUNT))]} ccc run python dummy.py --config dummy=True backbone=$backbone epoch_train=$epoch_train epoch_eval=$epoch_eval &
            s=$((s+1))
            wait_or_interrupt $GPU_COUNT $s
          done
        done
      done
    done
  done
fi

wait