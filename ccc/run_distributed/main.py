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
    return bool(re.match(pattern, file_path))


def parse_gpu_sources(gpu_file):
    if gpu_file is None:
        return []

    sources = [source.strip() for source in str(gpu_file).split(',') if source.strip()]
    return sources or [str(gpu_file).strip()]


def allocate_server_from_sources(file_paths):
    if not file_paths:
        raise ValueError("No GPU resource sources were provided.")

    direct_servers = []
    for file_path in file_paths:
        if is_server_as_gpu_filename(file_path):
            direct_servers.append(file_path)

    if direct_servers:
        return direct_servers[0], direct_servers[0]

    while True:
        for file_path in file_paths:
            with open(file_path, 'r+') as file:
                fcntl.flock(file, fcntl.LOCK_EX)
                try:
                    lines = file.readlines()
                    allocated_server = None

                    for i, line in enumerate(lines):
                        if not line.startswith("ALLOCATED"):
                            allocated_server = line.strip()
                            lines[i] = f"ALLOCATED {allocated_server}\n"
                            break

                    if allocated_server:
                        file.seek(0)
                        file.writelines(lines)
                        file.truncate()
                        return allocated_server, file_path
                finally:
                    fcntl.flock(file, fcntl.LOCK_UN)

        time.sleep(1)


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
    sources = parse_gpu_sources(gpu_file)

    # allocate a server/gpus and set it to env var SERVERS
    allocated_server, allocated_source = allocate_server_from_sources(sources)
    os.environ['SERVERS'] = allocated_server

    if is_dryrun:
        os.environ['DRYRUN'] = '1'

    # call main script
    script_path = os.path.join(os.path.dirname(__file__), 'main.sh')
    try:
        subprocess.run(['bash', script_path] + cmd, cwd=get_parent_dirname())
    finally:
        # release server
        release_server(allocated_source, allocated_server)
