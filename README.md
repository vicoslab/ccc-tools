# CCC Tools

Utility tools for [Conda Compute Cluster](https://github.com/vicoslab/ccc) enabling multi-node, multi-gpu distributed runs supporting distributed PyTorch convention with support for [SLURM](https://slurm.schedmd.com/documentation.html) jobs as well. The following operations are available:

* distributed run of scripts on selected servers: `ccc run`
* find available GPUs on cluster: `ccc gpus`

CAUTION: This tool relies on automatic SSH connection! You need to properly set up SSH keys without passphrase for distributed runs.

## Installation

Install using pip:

```bash
pip install git+https://github.com/vicoslab/ccc-tools
```

## Usage

Used for finding available GPUs split into tasks and calling your script on individual servers with distributed PyTorch convention (setting MASTER_PORT, MASTER_ADDR, WORLD_SIZE, and RANK_OFFSET). Example usage:

```bash
################################################################################
# (optional) load user/project configs and wait_or_interrupt function
source $(ccc file_cfg)   # for envs in user provided .ccc_config.sh or .slurm_config.sh
source $(ccc file_utils) # for wait_or_interrupt defined in utils.sh

# (optional) for SLURM environment, export SLURM_JOB_ARGS env var with non-GPU related requirements before calling ccc run
export SLURM_JOB_ARGS="--output=logs/%j-node-%t.out --time=01:00:00 --mem-per-gpu=8G --partition=gpu --cpus-per-task=16 --exclude=wn202"

################################################################################
# obtain list of available GPUs split into 4 tasks/jobs (each with a single GPU)
GPU_FILE=$(ccc gpus --on_cluster=cluster_info.json --gpus=1 --tasks=4 --hosts="HOST_A,HOST_B" --ignore_hosts="HOST_C")

# submit multiple tasks
ccc run $GPU_FILE python my_script.py --backbone=resnet50 &
ccc run $GPU_FILE python my_script.py --backbone=resnet101 &
ccc run $GPU_FILE python my_script.py --backbone=tu-convnext_base &
ccc run $GPU_FILE python my_script.py --backbone=tu-convnext_large &
ccc run $GPU_FILE python my_script.py --backbone=vit & # will wait until GPUs become available since there are only 4 tasks available 

# wait for completion of all (use wait_or_interrupt which properly handles CTRL+C to stop and cleanup in both CCC and SLURM)
wait_or_interrupt

# you need to manually cleanup GPU_FILE when finished
rm $GPU_FILE
```

Alternatively you can explicilty define SERVER string instead of GPU_FILE:

```bash
ccc run "localhost:0,1" python my_script.py --backbone=resnet50 &
```

See a more detailed example [here](example/EXPERIMENTS_MAIN.sh).

### User/project config and utils scripts

Provide an additional config to setup/load local environment (e.g., loading conda env or setting project env vars) on a running server host by creating `.ccc_config.sh` or `.slurm_config.sh`. Config file should be located within the same folder from where `ccc` tool is called. Note: config file will be created if it does not exist yet. 

You can load this file in your main bash script using: `source $(ccc file_cfg)`. CAUTION: This will run the script both inside your main script as well as on the host server right before calling your program.

Additionally, by adding `source $(ccc file_utils)` you can also use a bash function `wait_or_interrupt` that blocks until all background processes/jobs are finished while properly handling CTRL+C to stop and cleanup child processes under both CCC and SLURM.

### Support for SLURM

You can use this tool in [CCC](https://github.com/vicoslab/ccc) or [SLURM](https://slurm.schedmd.com/documentation.html) environment. When the `srun` command is detected, it will queue jobs to SLURM instead of manually running by SSH. Jobs will be run with `srun` in the background based on:

* arguments from the exported `SLURM_JOB_ARGS` with general job requirements (name, time, cpus)
* requested GPUs from the `ccc gpus` command, which is converted to SLURM GPU requirements and automatically passed along to `srun`

NOTE: User/project config on SLURM will be loaded only from `.slurm_config.sh`. Calling `ccc file_cfg` and `ccc file_utils` transparently provides paths to the corresponding config/utils files based on whether this is run under CCC or SLURM.

Example usage on SLURM:
```bash
...

# for SLURM environment, export SLURM_JOB_ARGS env var with non-GPU related requirements before calling ccc run
export SLURM_JOB_ARGS="--output=logs/%j-node-%t.out --time=01:00:00 --mem-per-gpu=8G --partition=gpu --cpus-per-task=16 --exclude=wn202"

# then submit multiple tasks
ccc run $GPU_FILE python my_script.py --backbone=resnet50 &
ccc run $GPU_FILE python my_script.py --backbone=resnet101 &
...
```

# Operations
Detailed list of operations

## Distributed run with `ccc run`
Run your script distributed on servers:

`ccc run [GPU_FILE or SERVER string] [your script] [args]` 

e.g.: `ccc run /tmp/ccc-gpus-dan28cua python train.py --config epoch=10` 

This tool will select the first available set of servers (i.e., a task) from /tmp/ccc-gpus-dan28cua, SSH to individual servers, and run `[your script] [args]` within the same workdir where ccc was called from (i.e., in the folder where the script calling ccc is located). The process blocks until your script is finished.

You can provide `.ccc_config.sh` (or `.slurm_config.sh`) to load your environment on each server (e.g., loading conda env). The config file should be located within the same folder from where the `ccc` tool is called. Note: the config file will be created if it does not exist yet. 

Any exported ENVIRONMENT variable with `CCC_` prefix will be passed to your script, but without the prefix.

CAUTION: This tool relies on automatic SSH connection! You need to properly set up SSH keys without passphrase for this to work.

## Find available GPUs with `ccc gpus`

Find available GPUs and save them to a tempfile, which you can pass to `ccc run` for distributed running. The filename is printed to stdout. NOTE: You need to manually clean up the file when finished.

```ccc gpus [ARGS]```

e.g.: `ccc gpus --on_cluster=cluster_info.json  --gpus=2 --tasks=4 --hosts="hostname1,hostname2(1+3),hostname3(1+2)" --ignore_hosts="hostname4"` 

This tool is used to save a list of available GPUs before running your script on servers with `ccc run`. 

Detailed description of `ccc gpus` command line:
```
usage: ccc gpus [-h] [-N NUM_GPUS] [-T NUM_TASKS] [--on_cluster ON_CLUSTER] [--min_gpus_per_host MIN_GPUS_PER_HOST] [--max_gpus_per_group MAX_GPUS_PER_GROUP] [--hosts HOSTS] [--ignore_hosts IGNORE_HOSTS]
       [--min_allowed_gpus MIN_ALLOWED_GPUS] [--gpus_as_single_host GPUS_AS_SINGLE_HOST] [--wait_for_available WAIT_FOR_AVAILABLE]

Select GPUs from a cluster or for local use. Selected GPUs are returned as a list of GPU ids per host.

options:
  -h, --help            show this help message and exit
  -N NUM_GPUS, --num_gpus NUM_GPUS, --gpus NUM_GPUS
            number of GPUs to select per one task (default: 1)
  -T NUM_TASKS, --num_tasks NUM_TASKS, --tasks NUM_TASKS
            number of tasks, i.e., num_gpus are selected for each task (default: 1)
  --on_cluster ON_CLUSTER
            when set to a JSON file with cluster info, it will use all cluster hosts (default: None
  --hosts HOSTS         comma-separated list of hosts to select GPUs from, in priority as listed; use only specific
            GPUs by adding "(ID1+ID2+ID3)" suffix to hostname, e.g., "HOST_A,HOST_B(1+2)" (default: all hosts)
  --ignore_hosts IGNORE_HOSTS
            comma-separated list of hosts to ignore; ignore only specific
            GPUs by adding "(ID1+ID2+ID3)" suffix to hostname, e.g., "HOST_A,HOST_B(1+2)" (default: None)
  --min_gpus_per_host MIN_GPUS_PER_HOST, --per_host MIN_GPUS_PER_HOST
            minimum number of GPUs to select per host (default: 1)
  --max_gpus_per_group MAX_GPUS_PER_GROUP, --out_group MAX_GPUS_PER_GROUP
            output groups of GPUs (e.g., 2 for 2 GPUs per node) (default: 0)
  --min_allowed_gpus MIN_ALLOWED_GPUS
            min allowed GPUs to be selected than requested
  --gpus_as_single_host GPUS_AS_SINGLE_HOST
            whether to group all GPUs on the same host as one host (default: True)
  
  --wait_for_available WAIT_FOR_AVAILABLE
            Time to wait for GPUs to become available, -1 == do not wait, 0 == wait indefinitely, >0 wait timeout (default: -1)
  
  --stdout              output list of GPUs to stdout instead of into a file (default: False)
  
  --slurm_exclusive_node
            use --exclusive flag for allocating the whole node (default: False)
  --slurm_gpus_per_node SLURM_GPUS_PER_NODE
            number of GPUs per node available in the cluster, required only when using --slurm_exclusive_node (default: 1)
Output format:
  # for cluster, one group of hosts per output line (num_gpus=6  min_gpus_per_host=2 max_gpus_per_output_group=6 )
  host1:0 host1:1 host1:2 host1:3 host2:0 host2:1        
     
  # for local machine one line without names
  0,1,2,3
    
Example usage:
  # from the whole cluster or its subset
  ccc gpus --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2
  ccc gpus --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2 --only_hosts host1 host2 # use only host1 and host2
  ccc gpus --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2 --ignore_hosts host1 host2 # ignore host1 and host2
  ccc gpus --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2 --ignore_hosts host1 host2(1+2) # ignore GPU only id 1 and 2 on host2, but use all others
  # from the local machine only
  ccc gpus --num_gpus 4 --min_allowed_gpus 2
```

### Cluster information file

Cluster information should be provided in JSON format as follows:

```
{
  "hosts": {
    "HOST_A": "https://host-a.patroller.cluster.com",
    "HOST_B": "https://host-b.patroller.cluster.com",
    "HOST_C": "https://host-c.patroller.cluster.com"
  },
  "host_priority": ["HOST_B", "HOST_A", "HOST_C"]
}
```

## List bash scripts for config/utils with `ccc file_*`

To load config or utils functions in your main bash script you can get path to files using `ccc`:
 * `ccc file_cfg`: path to your `.ccc_config.sh` or `.slurm_config.sh` configuration files
 * `ccc file_utils`: path to utils with `wait_or_interrupt` function

 Use with bash as:

 ```bash
 # for envs in user provided .ccc_config.sh or .slurm_config.sh
source $(ccc file_cfg)   

# for wait_or_interrupt defined in utils.sh
source $(ccc file_utils) 
```