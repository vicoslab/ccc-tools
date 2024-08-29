#!/bin/bash
# USER SETTINGS
# you may override config.sh variables here

# PROJECT SETTINGS

###################################################
######## ACTIVATE CONDA ENV
###################################################

USE_CONDA_HOME=${USE_CONDA_HOME:-~/conda}
USE_CONDA_ENV=${USE_CONDA_ENV:-ccc-tools}

. $USE_CONDA_HOME/etc/profile.d/conda.sh

conda activate $USE_CONDA_ENV
echo "Using conda env '$USE_CONDA_ENV'"

###################################################
######## DATA PARALLEL SETTINGS and PATHS
###################################################
export NCCL_P2P_DISABLE=1
export NCCL_IB_DISABLE=1
export NCCL_BLOCKING_WAIT=1
export NCCL_SHM_DISABLE=1
export NCCL_SOCKET_IFNAME=eth2

export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OMP_NUM_THREADS=1

export MY_CONFIG_ENV=/tmp