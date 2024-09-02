import subprocess
import os

from ccc.utils import get_parent_dirname

def run_slurm(gpu_file, cmd):
    
    # read SLURM GPU allocation arguments from gpu_file
    with open(gpu_file, 'r') as file:
        GPU_ARGS = " ".join([line.strip() for line in file.readlines()])

    # append GPU args to SLURM_JOB_ARGS for main.sh script
    os.environ['SLURM_JOB_ARGS'] = f"{os.environ['SLURM_JOB_ARGS']} {GPU_ARGS}" if 'SLURM_JOB_ARGS' in os.environ else GPU_ARGS

    # call main script
    script_path = os.path.join(os.path.dirname(__file__), 'main.sh')
    subprocess.run(['bash', script_path] + cmd, cwd=get_parent_dirname())

