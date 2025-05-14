"""  
Pipeline test utilities.  
"""  
import os  
import subprocess  
import signal  
import time  
import pytest  
from .defines import TEST_RUN_TIME, TERM_TIMEOUT  
  
def run_pipeline_generic(cmd: list[str], log_file: str, run_time: int = TEST_RUN_TIME, term_timeout: int = TERM_TIMEOUT):  
    """  
    Run a command, terminate after run_time, capture logs.  
    """  
    with open(log_file, 'w') as f:  
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  
        time.sleep(run_time)  
        proc.send_signal(signal.SIGTERM)  
        try:  
            proc.wait(timeout=term_timeout)  
        except subprocess.TimeoutExpired:  
            proc.kill()  
            pytest.fail(f"Command didn't terminate: {' '.join(cmd)}")  
        out, err = proc.communicate()  
        f.write('stdout:\n' + out.decode() + '\n')  
        f.write('stderr:\n' + err.decode() + '\n')  
        return out, err  
  
def run_pipeline_module_with_args(module: str, args: list[str], log_file: str, **kwargs):  
    return run_pipeline_generic(['python', '-u', '-m', module] + args, log_file, **kwargs)  
  
def run_pipeline_pythonpath_with_args(script: str, args: list[str], log_file: str, **kwargs):  
    env = os.environ.copy()  
    env['PYTHONPATH'] = './hailo_apps_infra'  
    return run_pipeline_generic(['python', '-u', script] + args, log_file, **kwargs)  
  
def run_pipeline_cli_with_args(cli: str, args: list[str], log_file: str, **kwargs):  
    return run_pipeline_generic([cli] + args, log_file, **kwargs)  