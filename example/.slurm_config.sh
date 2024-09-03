#!/bin/bash

# MY PROJECT/USER SETTINGS
module purge

module load Anaconda3

USE_CONDA_ENV=${USE_CONDA_ENV:-ccc-tools}

if ! conda env list | grep -q "$USE_CONDA_ENV"; then
    "Conda envirionment $USE_CONDA_ENV does not exists -- will create it first"
    conda env create -y -n "$ENV_NAME" python=3.11

    # and install ccc-tools
    pip install git+https://github.com/vicoslab/ccc-tools
fi

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

export MY_CONFIG_ENV=/tmp