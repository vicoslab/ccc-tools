import os,sys
import argparse
import math
import tempfile

from collections import OrderedDict as OrderedDict

from .cluter_info.patroller import PatrollerClusterInfo

def select_gpus(num_gpus=1, num_tasks=1, min_allowed_gpus=0, on_cluster=None, min_gpus_per_host=1, localhost="claims",
                only_hosts=None, ignore_hosts=(),):

    cluster = PatrollerClusterInfo(on_cluster)

    selected_devices = []    
    if on_cluster and len(on_cluster) > 0:
        status = cluster.get_cluster_status(only_hosts=only_hosts, ignore_hosts=ignore_hosts)

        # if there are not enough gpus on host to ensure min_gpus_per_node, then remove the host and its gpus from the list
        hosts = list(set([stat["host"] for stat in selected_devices]))
        for host in hosts:
            if len([stat for stat in selected_devices if stat["host"] == host]) < min_gpus_per_host:
                status = OrderedDict([(id, stat) for id, stat in status.items() if stat["host"] != host])
    else:
        devices = [x for x in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",") if x.strip() != ""]

        if len(devices) >= num_gpus:
            status = cluster.get_host_status(f"http://{localhost}", 'localhost')
        else:
            status = {}

    free_device_ids = [(id,data["host"]) for id, data in status.items() if len(data["claim"]["processes"]) == 0]

    #  select gpus in a group of min_gpus_per_node; repeat this until all gpus are selected
    host_gpus_per_task = []
    for _ in range(num_tasks):
        selected_devices = []
        while len(selected_devices) < num_gpus and len(free_device_ids) > 0:
            # get the number of free gpus per host
            free_hosts = set([host for id, host in free_device_ids])
            num_devices_per_host = {host: len([id for id, h in free_device_ids if  h == host]) for host in free_hosts}

            # remove host that do not have enough free gpus to ensure min_gpus_per_node
            free_device_ids = [(id, host) for id, host in free_device_ids if num_devices_per_host[host] >= min_gpus_per_host]

            # get next group of free gpus
            selected_devices.extend([status[free_device_ids.pop(0)[0]] for i in range(min(min_gpus_per_host, len(free_device_ids)))])

        if len(selected_devices) < num_gpus and (min_allowed_gpus <= 0 or len(selected_devices) < min_allowed_gpus):
            return {}

        # convert to list of gpu ids per host
        hosts = list(set([stat["host"] for stat in selected_devices]))

        host_gpus = {}
        for host in hosts:
            host_gpus[host] = sorted([str(stat["device"]["number"]) for stat in selected_devices if stat["host"] == host])

        host_gpus_per_task.append(host_gpus)
    return host_gpus_per_task

def parse_config(cmd):

    # parse arguments
    parser = argparse.ArgumentParser(description="Select gpus from a cluster or for local use. "
                                                 "Selected GPUs are returned as a list of gpu ids per host.")

    parser.add_argument("-N", "--num_gpus", "--gpus", type=int, default=1,
                        help="number of gpus to select per one task (default: %(default)s)")
    parser.add_argument("-T", "--num_tasks", "--tasks", type=int, default=1,
                        help="number of tasks, i.e. num_gpus are selected for each task  (default: %(default)s)")
    parser.add_argument("--on_cluster", type=str, default="",
                        help="when set to json file with cluster info then using all cluster hosts (default: None")
    parser.add_argument("--hosts", default="", type=str,
                        help="comma separated list of hosts to select gpus from, in priority as listed; use only specific GPUs by adding '(ID1+ID2+ID3)' suffix to hostname, e.g. 'HOST_A,HOST_B(1+2)' (default: all hosts)")
    parser.add_argument("--ignore_hosts", default="", type=str,
                        help="comma separated list of hosts to ignore; ignore only specific GPUs by adding '(ID1+ID2+ID3)' suffix to hostname, e.g. 'HOST_A,HOST_B(1+2)' (default: None)")
    parser.add_argument("--min_gpus_per_host", "--per_host", default=1, type=int,
                        help="minimum number of gpus to select per host (default: %(default)s)")
    parser.add_argument("--max_gpus_per_group", "--out_group", default=0, type=int,
                        help="output groups of gpus (e.g. 2 for 2 gpus per node) (default: %(default)s)")
    parser.add_argument("--min_allowed_gpus", type=int, default=-1,
                        help="min allow gpus to be selected than requested")
    parser.add_argument("--gpus_as_single_host", type=str, default="True",
                        help="whether to group all gpus on the same host as one host (default: True)")

    parser.add_argument("--wait_for_available", type=int, default=-1,
                        help="Time to wait for GPUs to become available, -1 == do not wait, 0 == wait indefinetly, >0 wait timeout (default: -1)")

    parser.add_argument("--stdout", action='store_true',
                        help="output list of gpus to stdout instead of into file (default: False)")

    parser.add_argument("--slurm_exclusive_node", action='store_true',
                        help="use --exclusive flag for allocating the whole node (default: False)")
    parser.add_argument("--slurm_gpus_per_node", type=int, default=1,
                        help="number of gpus per node available in cluster, required only when using --slurm_exclusive_node (default: 1)")



    return parser.parse_args(cmd)

def main(cmd):
    '''
    Select gpus from a cluster or for local use, and return it as a list of gpu ids per host.
    
    Output format:
        # for cluster, one group of hosts per output line (num_gpus=6  min_gpus_per_host=2 max_gpus_per_output_group=6 )
        host1:0 host1:1 host1:2 host1:3 host2:0 host2:1        
        
        # for local machine one line without names
        0,1,2,3
        
    Example usage:
        # from whole cluster or its subset
        python select_gpus.py --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2
        python select_gpus.py --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2 --only_hosts host1 host2
        python select_gpus.py --num_gpus 2 --on_cluster cluster_info.json --min_gpus_per_host 2 --ignore_hosts host1 host2
        # from local machine only
        python select_gpus.py --num_gpus 4 --min_allowed_gpus 2
    '''    
    args = parse_config(cmd)

    devices_for_tasks = select_gpus(args.num_gpus, args.num_tasks,
                                   min_allowed_gpus=args.min_allowed_gpus,
                                   on_cluster=args.on_cluster,
                                   min_gpus_per_host=args.min_gpus_per_host,
                                   only_hosts=args.hosts.split(",") if len(args.hosts) > 0 else None,
                                   ignore_hosts=args.ignore_hosts.split(","))

    def print_devices_per_host(host, gpus):
        if args.gpus_as_single_host.lower() == "true":
            return [f'{host}:{",".join(gpus)}']
        else:
            return [f'{host}:{g}' for g in gpus]


    if args.stdout:
        print_output = lambda s: print(s)
    else:
        temp_file = tempfile.NamedTemporaryFile(delete=False, prefix='ccc-gpus-')
        print_output = lambda s: temp_file.write((s+"\n").encode())
    
    for selected_devices in devices_for_tasks:
        # print result to stdout
        if not args.on_cluster:
            # print value for the only key in the dict
            print_output(",".join(list(selected_devices.values())[0]))
        else:
            single_task_display = []
            for host,gpus in selected_devices.items():
                if args.max_gpus_per_group > 0:
                    # split all gpus for a single host into multiple groups, each with at most max_gpus_per_group gpus
                    for g in range(math.ceil(len(gpus)/args.max_gpus_per_group)):
                        group_gpus = [gpus.pop(0) for i in range(min(args.max_gpus_per_group, len(gpus)))]
                        single_task_display.extend(print_devices_per_host(host, group_gpus))
                else:
                    # print all gpus for single host
                    single_task_display.extend(print_devices_per_host(host, gpus))
            print_output(" ".join(single_task_display))


    if not args.stdout:
        print(temp_file.name)
        temp_file.close()

def define_gpus_args(num_gpus, gpus_per_node, exclusive_nodes=True):
    
    # default cmd
    slurm_gpus_args = ["--gpus-per-task=1",
                       "--gpu-bind=single:1"]

    if exclusive_nodes:
        # use whole node exclusively
        nodes = int(math.ceil(num_gpus/gpus_per_node))
        slurm_gpus_args.append(f"--nodes={nodes}")
        slurm_gpus_args.append(f"--ntasks-per-node={gpus_per_node}")     # number of tasks
        slurm_gpus_args.append(f"--gres=gpu:{gpus_per_node}")	         # one GPU per task
        slurm_gpus_args.append("--exclusive")
    else:
        # run wherever there is space (shared node if another GPU available on that node
        slurm_gpus_args.append("--gres=gpu:1")	       # one GPU per task
        slurm_gpus_args.append(f"--ntasks={num_gpus}")	# total GPUs in one run
    
    return " ".join(slurm_gpus_args)

def main_slurm(cmd):
    args = parse_config(cmd)

    slurm_gpus_alloc = define_gpus_args(num_gpus=args.num_gpus, gpus_per_node=args.slurm_gpus_per_node, 
                                        exclusive_nodes=args.slurm_exclusive_node)

    if args.stdout:
        print(slurm_gpus_alloc)
    else:
        temp_file = tempfile.NamedTemporaryFile(delete=False, prefix='ccc-gpus-')
        temp_file.write((slurm_gpus_alloc+"\n").encode())

        print(temp_file.name)
        temp_file.close()

if __name__ == "__main__":
    main(sys.args[1:])