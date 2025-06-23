import os
import pytest
import logging


from hailo_apps.hailo_app_python.core.common.test_utils import (
    run_pipeline_module_with_args,
    run_pipeline_pythonpath_with_args,
    run_pipeline_cli_with_args,
    get_pipeline_args,
)

# Import installation utilities

from hailo_apps.hailo_app_python.core.common.installation_utils import detect_hailo_arch , detect_host_arch

from hailo_apps.hailo_app_python.core.common.camera_utils import is_rpi_camera_available

# Configure logging as needed.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_run_everything")

# Define configurations for five pipelines.
pipelines = [
    {
        "name": "detection",
        "module": "hailo_apps.hailo_app_python.apps.detection.detection_pipeline",
        "script": "hailo_apps/hailo_app_python/apps/detection/detection_pipeline.py",
        "cli": "hailo-detect"
    },
    {
        "name": "pose_estimation",
        "module": "hailo_apps.hailo_app_python.apps.pose_estimation.pose_estimation_pipeline",
        "script": "hailo_apps/hailo_app_python/apps/pose_estimation/pose_estimation_pipeline.py",
        "cli": "hailo-pose"
    },
    {
        "name": "depth",
        "module": "hailo_apps.hailo_app_python.apps.depth.depth_pipeline",
        "script": "hailo_apps/hailo_app_python/apps/depth/depth_pipeline.py",
        "cli": "hailo-depth"
    },
    {
        "name": "instance_segmentation",
        "module": "hailo_apps.hailo_app_python.apps.instance_segmentation.instance_segmentation_pipeline",
        "script": "hailo_apps/hailo_app_python/apps/instance_segmentation/instance_segmentation_pipeline.py",
        "cli": "hailo-seg"
    },
    {
        "name": "simple_detection",
        "module": "hailo_apps.hailo_app_python.apps.detection_simple.detection_pipeline_simple",
        "script": "hailo_apps/hailo_app_python/apps/detection_simple/detection_pipeline_simple.py",
        "cli": "hailo-detect-simple"
    },
    {
        "name": "face_recognition",
        "module": "hailo_apps.hailo_app_python.apps.face_recognition.face_recognition",
        "script": "hailo_apps/hailo_app_python/apps/face_recognition/face_recognition.py",
        "cli": "hailo-face-recon"
    },
]

# Map each run method label to its corresponding function.
run_methods = {
    "module": run_pipeline_module_with_args,
    "pythonpath": run_pipeline_pythonpath_with_args,
    "cli": run_pipeline_cli_with_args,
}


# Parameterize the test so that 'pipeline' and 'run_method_name' are provided.
@pytest.mark.parametrize("pipeline", pipelines, ids=[p["name"] for p in pipelines])
@pytest.mark.parametrize("run_method_name", list(run_methods.keys()))
def test_pipeline_run_defaults(pipeline, run_method_name):
    pipeline_name = pipeline["name"]
    run_method = run_methods[run_method_name]
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # ---------------------------
    # First run: Use empty arguments (defaults)
    # ---------------------------
    empty_args = []  # Empty args run as default behavior
    log_file_path_empty = os.path.join(log_dir, f"{pipeline_name}_{run_method_name}_empty.log")
    stdout, stderr = b"", b""
    if run_method_name == "module":
        cmd = ['python', '-u', '-m', pipeline["module"]] + empty_args
        print(f"Running command with empty args for {pipeline_name} ({run_method_name}): {' '.join(cmd)}")
        stdout, stderr = run_method(pipeline["module"], empty_args, log_file_path_empty)
    elif run_method_name == "pythonpath":
        cmd = ['python', '-u', pipeline["script"]] + empty_args
        print(f"Running command with empty args for {pipeline_name} ({run_method_name}): {' '.join(cmd)}")
        stdout, stderr = run_method(pipeline["script"], empty_args, log_file_path_empty)
    elif run_method_name == "cli":
        cmd = [pipeline["cli"]] + empty_args
        print(f"Running command with empty args for {pipeline_name} ({run_method_name}): {' '.join(cmd)}")
        stdout, stderr = run_method(pipeline["cli"], empty_args, log_file_path_empty)
    else:
        pytest.fail(f"Unknown run method: {run_method_name}")
    out_str = stdout.decode().lower() if stdout else ""
    err_str = stderr.decode().lower() if stderr else ""
    print(f"Empty args run for {pipeline_name} ({run_method_name}) Output:\n{out_str}")
    # Basic assertions for the empty args run.
    assert "error" not in err_str, f"{pipeline_name} ({run_method_name}) reported an error in empty-args run: {err_str}"
    assert "traceback" not in err_str, f"{pipeline_name} ({run_method_name}) traceback in empty-args run: {err_str}"

    # ---------------------------
    # Second run: With extra test arguments.
    # ---------------------------
    # For example, to include the USB camera:
    # The order is preserved—first the USB camera.
    extra_args = get_pipeline_args(suite="usb_camera")
    log_file_path_extra = os.path.join(log_dir, f"{pipeline_name}_{run_method_name}_extra.log")
    stdout_extra, stderr_extra = b"", b""
    if run_method_name == "module":
        cmd = ['python', '-u', '-m', pipeline["module"]] + extra_args
        print(f"Running command (extra args) for {pipeline_name} ({run_method_name}): {' '.join(cmd)}")
        stdout_extra, stderr_extra = run_method(pipeline["module"], extra_args, log_file_path_extra)
    elif run_method_name == "pythonpath":
        cmd = ['python', '-u', pipeline["script"]] + extra_args
        print(f"Running command (extra args) for {pipeline_name} ({run_method_name}): {' '.join(cmd)}")
        stdout_extra, stderr_extra = run_method(pipeline["script"], extra_args, log_file_path_extra)
    elif run_method_name == "cli":
        cmd = [pipeline["cli"]] + extra_args
        print(f"Running command (extra args) for {pipeline_name} ({run_method_name}): {' '.join(cmd)}")
        stdout_extra, stderr_extra = run_method(pipeline["cli"], extra_args, log_file_path_extra)
    else:
        pytest.fail(f"Unknown run method: {run_method_name}")
    out_extra_str = stdout_extra.decode().lower() if stdout_extra else ""
    err_extra_str = stderr_extra.decode().lower() if stderr_extra else ""
    print(f"Extra args run for {pipeline_name} ({run_method_name}) Output:\n{out_extra_str}")
    assert "error" not in err_extra_str, f"{pipeline_name} ({run_method_name}) reported error in extra run: {err_extra_str}"
    assert "traceback" not in err_extra_str, f"{pipeline_name} ({run_method_name}) traceback in extra run: {err_extra_str}"

    # --------- Third run: RPi camera (using common package function) ---------
    # Only run if the machine appears to be a Raspberry Pi.
    extra_args_rpi = get_pipeline_args(suite="rpi_camera")
    rpi_device = is_rpi_camera_available()
    stdout_rpi, stderr_rpi = b"", b""
    if ("rpi" == detect_host_arch() and rpi_device):
        log_file_path_rpi = os.path.join(log_dir, f"{pipeline_name}_{run_method_name}_rpi.log")
        if run_method_name == "module":
            cmd = ['python', '-u', '-m', pipeline["module"]] + extra_args_rpi
            print(f"Running rpi args for {pipeline_name} ({run_method_name}): {' '.join(cmd)}")
            stdout_rpi, stderr_rpi = run_method(pipeline["module"], extra_args_rpi, log_file_path_rpi)
        elif run_method_name == "pythonpath":
            cmd = ['python', '-u', pipeline["script"]] + extra_args_rpi
            print(f"Running rpi args for {pipeline_name} ({run_method_name}): {' '.join(cmd)}")
            stdout_rpi, stderr_rpi = run_method(pipeline["script"], extra_args_rpi, log_file_path_rpi)
        elif run_method_name == "cli":
            cmd = [pipeline["cli"]] + extra_args_rpi
            print(f"Running rpi args for {pipeline_name} ({run_method_name}): {' '.join(cmd)}")
            stdout_rpi, stderr_rpi = run_method(pipeline["cli"], extra_args_rpi, log_file_path_rpi)
        else:
            pytest.fail(f"Unknown run method: {run_method_name}")
        out_rpi_str = stdout_rpi.decode().lower() if stdout_rpi else ""
        err_rpi_str = stderr_rpi.decode().lower() if stderr_rpi else ""
        print(f"RPi args run output for {pipeline_name} ({run_method_name}):\n{out_rpi_str}")
        assert "error" not in err_rpi_str, f"{pipeline_name} ({run_method_name}) error in RPi run: {err_rpi_str}"
        assert "traceback" not in err_rpi_str, f"{pipeline_name} ({run_method_name}) traceback in RPi run: {err_rpi_str}"
    else:
        print("Not running on Raspberry Pi; skipping RPi camera run.")


if __name__ == "__main__":
    pytest.main(["-v", __file__])