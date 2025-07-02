import os
import pytest
import logging
from hailo_apps.hailo_app_python.core.common.test_utils import run_pipeline_pythonpath_with_args, get_pipeline_args
from hailo_apps.hailo_app_python.core.common.core import get_resource_path
from hailo_apps.hailo_app_python.core.common.defines import RETRAINING_MODEL_NAME, RESOURCES_MODELS_DIR_NAME, BARCODE_VIDEO_EXAMPLE_NAME, RESOURCES_ROOT_PATH_DEFAULT, DEFAULT_LOCAL_RESOURCES_PATH, RETRAINING_BARCODE_LABELS_JSON_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_run_everything")

def test_hef_8():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    args = get_pipeline_args(suite="hef_path", hef_path="/usr/local/hailo/resources/models/hailo8/yolov8s.hef")
    log_file_path_empty = os.path.join(log_dir, "hef_8.log")
    stdout, stderr = b"", b""
    cmd = ['python', '-u', "hailo_apps/hailo_app_python/apps/detection/detection_pipeline.py"] + args
    print(f"Running Hef 8 command: {' '.join(cmd)}")
    stdout, stderr = run_pipeline_pythonpath_with_args("hailo_apps/hailo_app_python/apps/detection/detection_pipeline.py", args, log_file_path_empty)
    out_str = stdout.decode().lower() if stdout else ""
    err_str = stderr.decode().lower() if stderr else ""
    print(f"Hef 8 Output:\n{out_str}")
    assert "error" not in err_str, f"Reported an error in Hef 8 run: {err_str}"
    assert "traceback" not in err_str, f"Traceback in Hef 8 run: {err_str}"

def test_hef_8l():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    args = get_pipeline_args(suite="hef_path", hef_path="/usr/local/hailo/resources/models/hailo8l/yolov8s.hef")
    log_file_path_empty = os.path.join(log_dir, "hef_8l.log")
    stdout, stderr = b"", b""
    cmd = ['python', '-u', "hailo_apps/hailo_app_python/apps/detection/detection_pipeline.py"] + args
    print(f"Running Hef 8l command: {' '.join(cmd)}")
    stdout, stderr = run_pipeline_pythonpath_with_args("hailo_apps/hailo_app_python/apps/detection/detection_pipeline.py", args, log_file_path_empty)
    out_str = stdout.decode().lower() if stdout else ""
    err_str = stderr.decode().lower() if stderr else ""
    print(f"Hef 8l Output:\n{out_str}")
    assert "error" not in err_str, f"Reported an error in Hef 8l run: {err_str}"
    assert "traceback" not in err_str, f"Traceback in Hef 8l run: {err_str}"

if __name__ == "__main__":
    pytest.main(["-v", __file__])