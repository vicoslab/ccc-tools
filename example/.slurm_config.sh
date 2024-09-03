#!/bin/bash

# MY PROJECT/USER SETTINGS
module purge

USE_CONDA_HOME=${USE_CONDA_HOME:-~/conda}
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
