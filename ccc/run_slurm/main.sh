#!/bin/bash

CMD_ARGS=$@

job_main() {
  # initial call to define the job and make a call to srun
  JOB_ARGS="${SLURM_JOB_ARGS}"  
  
  TASK_ARGS="${SLURM_TASK_ARGS}"
  TASK_ARGS="$TASK_ARGS -X" # disable status on SIGINT to force exit on CTR+C

  USE_SRUN="${USE_SRUN:-0}"
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
    cmd="srun -u $JOB_ARGS $TASK_ARGS $0 $CMD_ARGS"
  else
    # find how many tasks need to be started 
    N=$(echo "$cmd" | grep -oP '(?<=--ntasks=)\d+')

    cmd="sbatch $JOB_ARGS --wait --wrap \"for i in $(seq 1 $N); do srun -u $TASK_ARGS $0 $CMD_ARGS & done; wait\""
  fi

  if [ "$DRYRUN" == "1" ]; then
    echo RUN=task MASTER_PORT=$((RANDOM+24000)) $cmd
  else
    RUN=task MASTER_PORT=$((RANDOM+24000)) eval "$cmd"
  fi
}

task_main() {
  # entry-point for each parallel task
  echo "Started tasks for job $SLURM_JOB_ID"

  # set up env vars
  source "$(dirname $BASH_SOURCE)/config.sh"

  master_addr=$(expand_nodelist | head -n 1)
  export MASTER_ADDR=$master_addr

  export WORLD_SIZE=$SLURM_NTASKS
  export RANK_OFFSET=$SLURM_PROCID
  echo "SLURM_NTASKS=$SLURM_NTASKS"
  echo "SLURM_GPUS_PER_TASK=$SLURM_GPUS_PER_TASK"

  echo "WORLD_SIZE=$WORLD_SIZE"
  echo "RANK_OFFSET=$RANK_OFFSET"

  echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"

  echo "NODELIST="${SLURM_NODELIST}
  echo "JOB_NODELIST="${SLURM_JOB_NODELIST}

  echo "node=$SLURMD_NODENAME"
  echo "master=$MASTER_ADDR"
  ###################################################

  ###################################################
  # execute CMD with args  
  
  $CMD_ARGS

}

# Function to expand SLURM_JOB_NODELIST into individual hostnames the same as does scontrol show hostnames
# however, scontrol is not available inside container so we need manual function
expand_nodelist() {
    # Function to expand a node range (e.g., node[01-03], node[1-2], node[001-100])

    expand_node_range() {
        local node_range=$1

        # If the input matches the pattern node[...] 
        if [[ $node_range =~ \[(.*)\] ]]; then
            local prefix=${node_range%%\[*}  # Extract the prefix (e.g., "node", "gn")
            local content=${BASH_REMATCH[1]}  # Extract the content inside the brackets

            # Split content by both commas and semicolons
            local parts=()
            IFS=',' read -ra comma_parts <<< "$content"
            for part in "${comma_parts[@]}"; do
                IFS=';' read -ra semicolon_parts <<< "$part"
                parts+=("${semicolon_parts[@]}")
            done

            # Process each part (could be a range like "02-03" or individual node like "06")
            for part in "${parts[@]}"; do
                if [[ $part =~ ^([0-9]+)-([0-9]+)$ ]]; then
                    # Handle node range (e.g., "02-03" or "27-28")
                    local start=${BASH_REMATCH[1]}
                    local end=${BASH_REMATCH[2]}

                    # Determine the width for zero padding based on the larger of start or end
                    local width=${#start}
                    if [[ ${#end} -gt $width ]]; then
                        width=${#end}
                    fi

                    # Expand the range with appropriate zero padding
                    for i in $(seq -f "%0${width}g" "$start" "$end"); do
                        echo "${prefix}${i}"
                    done
                else
                    # Individual node (e.g., "06", "24", "32", "37")
                    echo "${prefix}${part}"
                fi
            done
        else
            # If no brackets, just return the node as is
            echo "$node_range"
        fi
    }

    # Get the SLURM_JOB_NODELIST
    local NODELIST=$SLURM_JOB_NODELIST

    # Prepare an empty array to hold expanded nodes
    local expanded_nodes=()

    # Split the nodelist into individual node expressions
    # We need to be careful about commas - they can be inside brackets or separators between node groups
    local current_expr=""
    local bracket_count=0
    local i=0
    
    while [[ $i -lt ${#NODELIST} ]]; do
        local char="${NODELIST:$i:1}"
        
        if [[ $char == "[" ]]; then
            ((bracket_count++))
            current_expr+="$char"
        elif [[ $char == "]" ]]; then
            ((bracket_count--))
            current_expr+="$char"
        elif [[ $char == "," && $bracket_count -eq 0 ]]; then
            # This comma is a separator between node groups
            if [[ -n $current_expr ]]; then
                expanded_nodes+=($(expand_node_range "$current_expr"))
                current_expr=""
            fi
        else
            current_expr+="$char"
        fi
        
        ((i++))
    done
    
    # Process the last expression
    if [[ -n $current_expr ]]; then
        expanded_nodes+=($(expand_node_range "$current_expr"))
    fi

    # Print the expanded list of hostnames
    for hostname in "${expanded_nodes[@]}"; do
        echo "$hostname"
    done
}

if [ "${RUN}" = "task" ]; then
  task_main
else
  job_main
fi
