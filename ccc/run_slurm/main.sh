#!/bin/bash

CMD_ARGS=$@

job_main() {
  # initial call to define the job and make a call to srun
  JOB_ARGS="${SLURM_JOB_ARGS}"  
  
  TASK_ARGS="${SLURM_TASK_ARGS}"
  TASK_ARGS="$TASK_ARGS -X" # disable status on SIGINT to force exit on CTR+C

  USE_SRUN=0
  if [ -n "$DISPLAY" ] && [ "${DISABLE_X11}" != "1" ]; then
    TASK_ARGS="--x11 $TASK_ARGS"
    
    # use SRUN directly if requested --x11
    USE_SRUN=1 
  fi

  # pass all needed env vars (passthrough any CCC_ prefix variable, but without the prefix)
  for var in $(printenv | grep '^CCC_'); do
      # Remove the CCC_ prefix and directly export
      export $(printenv | grep '^CCC_' | sed 's/^CCC_//')
  done
  
  # call srun on this script if requested interactive/blocking or sbtach otherwise
  if [ "$USE_SRUN" == "1" ]; then
    cmd=srun -u $JOB_ARGS $TASK_ARGS $0 $CMD_ARGS
  else
    cmd=sbatch $JOB_ARGS --wait --wrap "srun -u $TASK_ARGS $0 $CMD_ARGS"
  fi

  if "$DRYRUN" == "1" ]; then
    echo RUN=task MASTER_PORT=$((RANDOM+24000)) $cmd
  else
    RUN=task MASTER_PORT=$((RANDOM+24000)) $cmd
  fi
}

task_main() {
  # entry-point for each parallel task
  echo "Started tasks for job $SLURM_JOB_ID"

  # set up env vars
  source "$(dirname $BASH_SOURCE)/config.sh"

  master_addr=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
  export MASTER_ADDR=$master_addr

  export WORLD_SIZE=$SLURM_NTASKS
  export RANK_OFFSET=$SLURM_PROCID
  echo "existing CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
  echo "SLURM_NTASKS=$SLURM_NTASKS"
  echo "SLURM_GPUS_PER_TASK=$SLURM_GPUS_PER_TASK"

  echo "WORLD_SIZE=$WORLD_SIZE"
  echo "RANK_OFFSET=$RANK_OFFSET"

  echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"

  echo "NODELIST="${SLURM_NODELIST}
  echo "JOB_NODELIST="${SLURM_JOB_NODELIST}

  echo "master=$MASTER_ADDR"
  ###################################################

  ###################################################
  # execute CMD with args  
  
  $CMD_ARGS

}

if [ "${RUN}" = "task" ]; then
  task_main
else
  job_main
fi
