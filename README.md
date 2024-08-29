## CCC Tools

Utility tools for Conda Compute Cluster

# Installation

Install using pip:

```bash
pip install git+https://github.com/vicoslab/ccc-tools
```

# Distributed run
Run your script distributed on servers:

`SERVERS="SERVER_LIST" ccc run [your script] [args]` 

e.g.: `SERVERS="localhost:0,1,2,4" ccc run python train.py --config epoch=10` 

This tool will ssh to individual servers and run `[your script] [args]` within the same workdir where ccc was called from (i.e., in folder where script calling ccc is located).

You can provide `.ccc_config.sh` to load your envirionment on each server (e.g., loading conda env). Config file should be located within the same folder from where `ccc` tool is called. Note: config file will be created if does not exist yet.

CAUTION: This tool relies on automatic SSH connection! You need to properly setup ssh keys without passphrase for this to work.

# Find available gpus

Find available gpus that you can use for distributed running

`ccc gpus [ARGS]` 

e.g.: `ccc gpus --on_cluster=cluster_info.json  --gpus=2 --tasks=4 --hosts="hostname1,hostname2(1+3),hostname3(1+2)" --ignore_hosts="hostname4"`

This tool is used before running your script on servers with `ccc run`:

```bash
# obtain list of available gpus split into four tasks/jobs (each with a single gpu)
mapfile -t GPU_LIST < <(ccc gpus --on_cluster=cluster_info.json --gpus=1 --tasks=4 --hosts="HOST_A,HOST_B" --ignore_hosts="HOST_C")

SERVERS=${GPU_LIST[0]} ccc run python my_script.py --backbone=resnet50 &
SERVERS=${GPU_LIST[1]} ccc run python my_script.py --backbone=resnet101 &
SERVERS=${GPU_LIST[3]} ccc run python my_script.py --backbone=tu-convnext_base &
SERVERS=${GPU_LIST[4]} ccc run python my_script.py --backbone=tu-convnext_large &

```

Detailed description of `ccc gpus` command line:
```
usage: ccc gpus [-h] [-N NUM_GPUS] [-T NUM_TASKS] [--on_cluster ON_CLUSTER] [--min_gpus_per_host MIN_GPUS_PER_HOST] [--max_gpus_per_group MAX_GPUS_PER_GROUP] [--hosts HOSTS] [--ignore_hosts IGNORE_HOSTS]
           [--min_allowed_gpus MIN_ALLOWED_GPUS] [--gpus_as_single_host GPUS_AS_SINGLE_HOST] [--wait_for_available WAIT_FOR_AVAILABLE]

Select gpus from a cluster or for local use. Selected GPUs are returned as a list of gpu ids per host.

options:
  -h, --help            show this help message and exit
  -N NUM_GPUS, --num_gpus NUM_GPUS, --gpus NUM_GPUS
                        number of gpus to select per one task (default: 1)
  -T NUM_TASKS, --num_tasks NUM_TASKS, --tasks NUM_TASKS
                        number of tasks, i.e. num_gpus are selected for each task (default: 1)
  --on_cluster ON_CLUSTER
                        when set to json file with cluster info then using all cluster hosts (default: None
  --min_gpus_per_host MIN_GPUS_PER_HOST, --per_host MIN_GPUS_PER_HOST
                        minimum number of gpus to select per host (default: 1)
  --max_gpus_per_group MAX_GPUS_PER_GROUP, --out_group MAX_GPUS_PER_GROUP
                        output groups of gpus (e.g. 2 for 2 gpus per node) (default: 0)
  --hosts HOSTS         comma separated list of hosts to select gpus from, in priority as listed (default: all hosts)
  --ignore_hosts IGNORE_HOSTS
                        comma separated list of hosts to ignore (default: None)
  --min_allowed_gpus MIN_ALLOWED_GPUS
                        min allow gpus to be selected than requested
  --gpus_as_single_host GPUS_AS_SINGLE_HOST
                        weather to group all gpus on the same host as one host (default: True)
  --wait_for_available WAIT_FOR_AVAILABLE
                        Time to wait for GPUs to become available, -1 == do not wait, 0 == wait indefinetly, >0 wait timeout (default: -1)

Output format:
    # for cluster, one group of hosts per output line (num_gpus=6  min_gpus_per_host=2 max_gpus_per_output_group=6 )
    host1:0 host1:1 host1:2 host1:3 host2:0 host2:1        
       
    # for local machine one line without names
    0,1,2,3
        
Example usage:
    # from whole cluster or its subset
    ccc gpus --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2
    ccc gpus --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2 --only_hosts host1 host2 # use only host1 and host2
    ccc gpus --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2 --ignore_hosts host1 host2 # ignore host1 and host2
    ccc gpus --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2 --ignore_hosts host1 host2(1+2) # ignore GPU only id 1 and 2 on host2, but use all others
    # from local machine only
    ccc gpus --num_gpus 4 --min_allowed_gpus 2
```

## Cluster information file

Cluster information should be provided in JSON format as follows:

```
{
  "hosts": {
    "HOST_A": "https://host-a.patroller.cluster.com",
    "HOST_B": "https://host-b.patroller.cluster.com",
    "HOST_C": "https://host-c.patroller.cluster.com",
  },
  "host_priority": ["HOST_B", "HOST_A", "HOST_C"]
}
```