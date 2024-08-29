import subprocess
import os,sys
import argparse

import os


def get_parent_dirname():
    """
    Retrieves the filename of the first parent script that called the current script.
    """
    import psutil
    # Get the current process ID
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)

    # Get the parent process
    parent_process = current_process.parent()

    # Check if the parent process exists
    if parent_process:
        # Get the command line arguments of the parent process
        cmdline = parent_process.cmdline()
        
        # The first argument is usually the script name
        if cmdline and len(cmdline) > 1:
            return os.path.dirname(os.path.abspath(cmdline[1]))

    return None

def run_distributed(cmd):    
    script_path = os.path.join(os.path.dirname(__file__), 'run_distributed','main.sh')
    subprocess.run(['bash', script_path] + cmd, cwd=get_parent_dirname())

def main():    
    parser = argparse.ArgumentParser(description="Utility tool for Conda Compute Cluster "
                                                 "Operations: 'run' or 'gpus'")
    
    parser.add_argument('operation', choices=['run', 'gpus', 'file_cfg', 'file_utils'], help='Operation to perform')

    args = parser.parse_args(sys.argv[1:2])  

    if args.operation == "run":
        run_distributed(sys.argv[2:])
    elif args.operation == "gpus":
        from .select_gpus.main import main as select_gpus
        select_gpus(sys.argv[2:])
    elif args.operation == "file_cfg":
        print(os.path.abspath(os.path.join(get_parent_dirname(),'.ccc_config.sh')))
    elif args.operation == "file_utils":
        print(os.path.abspath(os.path.join(os.path.dirname(__file__), 'run_distributed','utils.sh')))

if __name__ == '__main__':
    main()