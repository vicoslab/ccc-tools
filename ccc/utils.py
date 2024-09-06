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

    return os.path.abspath('.')
