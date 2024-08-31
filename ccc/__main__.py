import subprocess
import os,sys
import argparse

import os

import fcntl
import time

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

def allocate_server(file_path):
    while True:
        with open(file_path, 'r+') as file:
            # Lock the file for reading and writing
            fcntl.flock(file, fcntl.LOCK_EX)
            try:
                # Read all lines from the file
                lines = file.readlines()
                allocated_server = None

                # Find the first line that does not start with "ALLOCATED"
                for i, line in enumerate(lines):
                    if not line.startswith("ALLOCATED"):
                        allocated_server = line.strip()
                        lines[i] = f"ALLOCATED {allocated_server}\n"  # Add "ALLOCATED" prefix
                        break

                if allocated_server:
                    # Write back the modified lines to the file
                    file.seek(0)  # Move to the beginning of the file
                    file.writelines(lines)
                    file.truncate()  # Remove any leftover lines

                    return allocated_server
                else:
                    # Sleep for a while before retrying
                    time.sleep(1)  
            finally:
                # Unlock the file
                fcntl.flock(file, fcntl.LOCK_UN)


def release_server(file_path, server_name):
    with open(file_path, 'r+') as file:
        # Lock the file for reading and writing
        fcntl.flock(file, fcntl.LOCK_EX)
        try:
            # Read all lines from the file
            lines = file.readlines()

            # Find the line with the specified server name and remove the "ALLOCATED" prefix
            for i, line in enumerate(lines):
                if line.endswith(f"{server_name}\n"):
                    lines[i] = line.replace("ALLOCATED ", "")
                    break

            # Write back the modified lines to the file
            file.seek(0)  # Move to the beginning of the file
            file.writelines(lines)
            file.truncate()  # Remove any leftover lines
        
        finally:
            # Unlock the file
            fcntl.flock(file, fcntl.LOCK_UN)

def run_distributed(gpu_file, cmd):
    # allocate a server/gpus and set it to env var SERVERS
    os.environ['SERVERS'] = allocate_server(gpu_file)
    
    # call main script
    script_path = os.path.join(os.path.dirname(__file__), 'run_distributed','main.sh')
    subprocess.run(['bash', script_path] + cmd, cwd=get_parent_dirname())

    # release server
    release_server(gpu_file, os.environ['SERVERS'])

def main():    
    parser = argparse.ArgumentParser(description="Utility tool for Conda Compute Cluster "
                                                 "Operations: 'run' or 'gpus'")
    
    parser.add_argument('operation', choices=['run', 'gpus', 'file_cfg', 'file_utils'], help='Operation to perform')

    args = parser.parse_args(sys.argv[1:2])  

    if args.operation == "run":
        run_distributed(sys.argv[2], sys.argv[3:])
    elif args.operation == "gpus":
        from .select_gpus.main import main as select_gpus
        select_gpus(sys.argv[2:])
    elif args.operation == "file_cfg":
        print(os.path.abspath(os.path.join(get_parent_dirname(),'.ccc_config.sh')))
    elif args.operation == "file_utils":
        print(os.path.abspath(os.path.join(os.path.dirname(__file__), 'run_distributed','utils.sh')))

if __name__ == '__main__':
    main()