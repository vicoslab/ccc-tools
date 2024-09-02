#!/bin/bash

# You need to set the following config values
# GPUS_PER_NODE=4
# STORAGE_DIR=/PATH/TO/STORAGE

# HPC-Vega:
# GPUS_PER_NODE=4
# STORAGE_DIR=/ceph/hpc/data/FRI/tabernikd/

# HPC-Arnes:
GPUS_PER_NODE=2
STORAGE_DIR=/d/hpc/projects/FRI/tabernikd/

# MY PROJECT/USER SETTINGS
module purge

USE_CONDA_HOME=${USE_CONDA_HOME:-${STORAGE_DIR}/user/conda}
USE_CONDA_ENV=${USE_CONDA_ENV:-ccc-tools}

echo "Loading conda env ..."
. ${USE_CONDA_HOME}/etc/profile.d/conda.sh

conda activate $USE_CONDA_ENV
echo "Using conda env '$USE_CONDA_ENV'"

###################################################
######## SLURM DATA PARALLEL SETTINGS
###################################################
export NCCL_P2P_DISABLE=1
export NCCL_IB_DISABLE=1
export NCCL_BLOCKING_WAIT=1
export NCCL_PROTO=SIMPLE

export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=INIT,GRAPH,ENV
