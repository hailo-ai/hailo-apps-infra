import os
import subprocess
import signal
import time
import pytest
from hailo_common.get_usb_camera import get_usb_video_devices


TEST_RUN_TIME = 10  # seconds

def run_pipeline_generic(cmd, log_file_path, run_time=TEST_RUN_TIME, term_timeout=5):
    """
    Runs a pipeline command, logs stdout and stderr to log_file_path,
    and forces termination after run_time seconds.
    """
    with open(log_file_path, "w") as log_file:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(run_time)
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=term_timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            pytest.fail(f"Pipeline command '{' '.join(cmd)}' did not terminate within {term_timeout} seconds.")
        stdout, stderr = process.communicate()
        log_file.write("stdout:\n" + stdout.decode() + "\n")
        log_file.write("stderr:\n" + stderr.decode() + "\n")
        return stdout, stderr

def run_pipeline_module_with_args(module_name, args, log_file_path, run_time=TEST_RUN_TIME, term_timeout=5):
    """
    Runs a pipeline as a module, e.g.:
    python -u -m hailo_apps_infra.pipelines.hailo_pipelines.<pipeline> <args...>
    """
    cmd = ['python', '-u', '-m', module_name] + args
    return run_pipeline_generic(cmd, log_file_path, run_time, term_timeout)

def run_pipeline_pythonpath_with_args(script_path, args, log_file_path, run_time=TEST_RUN_TIME, term_timeout=5):
    """
    Runs a pipeline using the PYTHONPATH environment variable, e.g.:
    PYTHONPATH=./hailo_apps_infra python -u <script_path> <args...>
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = "./hailo_apps_infra"
    cmd = ['python', '-u', script_path] + args
    with open(log_file_path, "w") as log_file:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        time.sleep(run_time)
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=term_timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            pytest.fail(f"Pipeline command '{' '.join(cmd)}' did not terminate within {term_timeout} seconds.")
        stdout, stderr = process.communicate()
        log_file.write("stdout:\n" + stdout.decode() + "\n")
        log_file.write("stderr:\n" + stderr.decode() + "\n")
        return stdout, stderr

def run_pipeline_cli_with_args(cli_command, args, log_file_path, run_time=TEST_RUN_TIME, term_timeout=5):
    """
    Runs a pipeline using its CLI entry point, e.g.:
    hailo-simple-detect <args...>
    """
    cmd = [cli_command] + args
    return run_pipeline_generic(cmd, log_file_path, run_time, term_timeout)


def get_pipeline_args(suite="default",hef_path=None, override_usb_camera=None , override_video_input=None):
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
                devices = get_usb_video_devices()
                device = devices[0] if devices else "/dev/video0"
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
            args += ["--labels-json", "resources/labels.json"]
    return args