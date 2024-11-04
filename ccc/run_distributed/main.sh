#!/bin/bash

CMD_ARGS=$@

job_main() {
  # initial call that will delegate job into servers
  # SERVERS env var should be list of servers ang gpu ids per each server (e.g. "donbot:0,1,2,3 morbo:2,3 calculon:1,0"
  # first count number of servers and GPUs to get the world size
  num_gpus="${SERVERS//[^,]}"
  num_gpus="${#num_gpus}"

  num_servers="${SERVERS//[^ ]}"
  num_servers="${#num_servers}"

  WORLD_SIZE=$((num_gpus+num_servers+1))
  RANK_OFFSET=0
  MASTER_PORT=$((RANDOM+24000))

  IFS=' ' read -ra ADDR_LIST <<< "$SERVERS"
  for ADDR in "${ADDR_LIST[@]}"; do
    # address is in format: <SEVER_NAME>:<CUDA_VISIBLE_DEVICES> (e.g. donbot:0,1,2,3)
    IFS=':' read -ra NAME_ID <<< "$ADDR"
    SERVER_NAME=${NAME_ID[0]}
    CUDA_VISIBLE_DEVICES=${NAME_ID[1]}

    # set master to first server
    if [ -z "$MASTER_ADDR" ]; then
      MASTER_ADDR=$SERVER_NAME
    fi

    # pass to ssh all needed env vars (passthrough any CCC_ prefix variable, but without the prefix)
    
    # Initialize an empty variable to hold the concatenated env vars
    ENVS=""

    # Loop through all environment variables that start with CCC_
    for var in $(printenv | grep '^CCC_'); do
        # Remove the CCC_ prefix and append to ENVS
        var_name=$(echo "$var" | sed 's/^CCC_//')
        ENVS+="$var_name "
    done

    # Trim the trailing space
    ENVS=$(echo "$ENVS" | sed 's/[[:space:]]*$//')

    # add system config variables
    ENVS="$ENVS CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
    
    ENVS="$ENVS MASTER_PORT=$MASTER_PORT"
    ENVS="$ENVS MASTER_ADDR=$MASTER_ADDR"
    ENVS="$ENVS WORLD_SIZE=$WORLD_SIZE"
    ENVS="$ENVS RANK_OFFSET=$RANK_OFFSET"
    ENVS="$ENVS DISABLE_X11=$DISABLE_X11"
    
    if [ -n "$USE_CONDA_ENV" ]; then
      ENVS="$ENVS USE_CONDA_ENV=$USE_CONDA_ENV"
    fi
    ENVS="$ENVS WORKDIR=$(pwd)"

    export ENVS
    export SERVER_NAME
    # run ssh connection in child background process
    RUN=ssh $(realpath $0) $CMD_ARGS &

    # increase world rank offset by the number of gpus
    num_gpus="${CUDA_VISIBLE_DEVICES//[^,]}"
    num_gpus="${#num_gpus}"
    RANK_OFFSET=$((RANK_OFFSET + num_gpus + 1))
  done

  # do cleanup of child processes on CTRL+C
  trap "kill 0" SIGINT  
  wait
}

ssh_main() {
  SSH_ARGS="-t -t -o StrictHostKeyChecking=no"
  if [ "${DISABLE_X11}" != "1" ]; then
    SSH_ARGS="-Y $SSH_ARGS"
  fi

  # call main task function on server (use -t -t to allow exiting remote process in interuption)  
  cmd=ssh $SSH_ARGS $SERVER_NAME RUN=task $ENVS $(realpath $0) $(printf "%q " "$CMD_ARGS")
  
  if [ "$DRYRUN" == "1" ]; then
    echo $cmd
  else
    exec $cmd
  fi
}

task_main() {
  # Set up signal trap to catch Ctrl+C
  trap "exit" SIGINT

  cd $WORKDIR

  # set up env vars
  source "$(dirname $BASH_SOURCE)/config.sh"

  echo "NODE=$HOSTNAME CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES WORLD_SIZE=$WORLD_SIZE RANK_OFFSET=$RANK_OFFSET master=$MASTER_ADDR"

  ###################################################
  # execute CMD with args  
  $CMD_ARGS
}

if [ "${RUN}" = "ssh" ]; then
  ssh_main
elif [ "${RUN}" = "task" ]; then
  task_main
else
  job_main
fi