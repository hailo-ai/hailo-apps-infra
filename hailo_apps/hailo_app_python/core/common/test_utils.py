"""  
Pipeline test utilities.  
"""  
import os  
import subprocess  
import signal  
import time  
import pytest  
from .defines import TEST_RUN_TIME, TERM_TIMEOUT  

def get_pipeline_args(suite="default",hef_path=None, override_usb_camera=None , override_video_input=None, override_labels_json=None):
    """
    Returns a list of additional arguments based on the specified test suite.
    
    Supported suites (comma‑separated):
      - "usb_camera": Set the '--input' argument to the USB camera device
                     determined by get_usb_video_devices().
      - "rpi_camera": Set the '--input' argument to "rpi".
      - "hef_path":   Set the '--hef-path' argument to the user-specified HEF path
                     using the USER_HEF environment variable (or a fallback value).
      - "video_file": Set the '--input' argument to a video file ("resources/example.mp4").
      - "disable_sync": Append the flag "--disable-sync".
      - "disable_callback": Append the flag "--disable-callback".
      - "show_fps": Append the flag "--show-fps".
      - "dump_dot": Append the flag "--dump-dot".
      - "labels": Append the flag "--labels-json" followed by "resources/labels.json".
      - "ui": Append the flag "--ui".
      - "visualize": Append the flag "--visualize".
      - "mode-train": Set the '--mode' argument to train.
      - "mode-delete": Set the '--mode' argument to delete.
      - "mode-run": Set the '--mode' argument to run.

    If suite is "default", returns an empty list (i.e. no extra test arguments).
    """
    # Start with no extra arguments.
    args = []
    if suite == "default":
        return args

    suite_names = [s.strip() for s in suite.split(",")]
    for s in suite_names:
        if s == "usb_camera":
            # If override_usb_camera is provided, use it; otherwise, get the USB camera device.
            if override_usb_camera:
                device = override_usb_camera
            else:
                device = "usb"
            # Append or override --input (here we simply add the argument)
            args += ["--input", device]
        elif s == "rpi_camera":
            args += ["--input", "rpi"]
        elif s == "hef_path":
            hef = hef_path
            args += ["--hef-path", hef]
        elif s == "video_file":
            # If override_video_input is provided, use it; otherwise, use the default video file.
            if override_video_input:
                video_file = override_video_input
            else:
                video_file = "resources/example.mp4"
            # Append or override --input (here we simply add the argument)
            args += ["--input", video_file]
        elif s == "disable_sync":
            args.append("--disable-sync")
        elif s == "disable_callback":
            args.append("--disable-callback")
        elif s == "show_fps":
            args.append("--show-fps")
        elif s == "dump_dot":
            args.append("--dump-dot")
        elif s == "labels":
            # If override_labels_json is provided, use it; otherwise, use the default json file.
            if override_labels_json:
                json_file = override_labels_json
            else:
                json_file = "resources/labels.json"
            # Append or override --input (here we simply add the argument)
            args += ["--labels-json", json_file]
        elif s == "ui":
            args.append("--ui")
        elif s == "visualize":
            args.append("--visualize")
        elif s == "mode-train":
            args += ["--mode", "train"]
        elif s == "mode-delete":
            args += ["--mode", "delete"]
        elif s == "mode-run":
            args += ["--mode", "run"]
    return args

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