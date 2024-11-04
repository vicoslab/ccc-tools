import subprocess
import os

import fcntl
import time

import re

from ccc.utils import get_parent_dirname

def is_server_as_gpu_filename(file_path):
    # if file exists then use it 
    if os.path.exists(file_path):
        return False
    
    # check if file contains valid server string
    pattern = r'^\w+(:\d+(,\d+)*)?(\s+\w+(:\d+(,\d+)*)?)*$'
    return re.match(pattern, file_path)

def allocate_server(file_path):
    # just pass value of file_path if this already contains valid server string
    if is_server_as_gpu_filename(file_path):
        return file_path
    
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
    # skip if file_path already contains valid server string
    if is_server_as_gpu_filename(file_path):
        return 
    
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

def run_distributed(gpu_file, cmd, is_dryrun=False):
    # allocate a server/gpus and set it to env var SERVERS
    os.environ['SERVERS'] = allocate_server(gpu_file)
    
    if is_dryrun:
        os.environ['DRYRUN'] = 1

    # call main script
    script_path = os.path.join(os.path.dirname(__file__), 'main.sh')
    subprocess.run(['bash', script_path] + cmd, cwd=get_parent_dirname())

    # release server
    release_server(gpu_file, os.environ['SERVERS'])
