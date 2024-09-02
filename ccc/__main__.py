import os,sys
import argparse

import os

from ccc.utils import get_parent_dirname

def is_slurm_environment():
    """
    Check if the current environment is a SLURM login node.

    Returns:
        bool: True if in a SLURM environment, False otherwise.
    """
    # Check for SLURM-related environment variables
    slurm_submit_host = os.environ.get('SLURM_SUBMIT_HOST')
    slurm_cluster_name = os.environ.get('SLURM_CLUSTER_NAME')

    # Determine if we are in a SLURM environment
    return slurm_submit_host or slurm_cluster_name

def main():    
    # check if in SLURM envirionemnt
    
    parser = argparse.ArgumentParser(description="Utility tool for Conda Compute Cluster "
                                                 "Operations: 'run' or 'gpus'")
    
    parser.add_argument('operation', choices=['run', 'gpus', 'file_cfg', 'file_utils'], help='Operation to perform')

    args = parser.parse_args(sys.argv[1:2])  
    if is_slurm_environment(): 
        from ccc.run_slurm.main import run_slurm
        from ccc.gpus.main import main_slurm as define_gpus_slurm

        if args.operation == "run":
            run_slurm(sys.argv[2], sys.argv[3:])
        elif args.operation == "gpus":
            define_gpus_slurm(sys.argv[2:])
        elif args.operation == "file_cfg":
            print(os.path.abspath(os.path.join(get_parent_dirname(),'.slurm_config.sh')))
        elif args.operation == "file_utils":
            print(os.path.abspath(os.path.join(os.path.dirname(__file__), 'run_slurm','utils.sh')))
    
    else:
        from ccc.run_distributed.main import run_distributed
        from ccc.gpus.main import main as allocate_gpus_ccc


        if args.operation == "run":
            run_distributed(sys.argv[2], sys.argv[3:])
        elif args.operation == "gpus":
            allocate_gpus_ccc(sys.argv[2:])
        elif args.operation == "file_cfg":
            print(os.path.abspath(os.path.join(get_parent_dirname(),'.ccc_config.sh')))
        elif args.operation == "file_utils":
            print(os.path.abspath(os.path.join(os.path.dirname(__file__), 'run_distributed','utils.sh')))

if __name__ == '__main__':
    main()