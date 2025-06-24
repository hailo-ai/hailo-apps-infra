import os
from pathlib import Path
import pytest
import logging
from hailo_apps.hailo_app_python.core.common.test_utils import run_pipeline_pythonpath_with_args, get_pipeline_args
from hailo_apps.hailo_app_python.core.common.core import get_resource_path
from hailo_apps.hailo_app_python.core.common.defines import RETRAINING_MODEL_NAME, RESOURCES_MODELS_DIR_NAME, BARCODE_VIDEO_EXAMPLE_NAME, RESOURCES_ROOT_PATH_DEFAULT, DEFAULT_LOCAL_RESOURCES_PATH, RETRAINING_BARCODE_LABELS_JSON_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_run_everything")

def test_retraining_defaults():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    args = get_pipeline_args(
        suite="labels,video_file,hef_path", 
        hef_path=str(get_resource_path(pipeline_name=None, resource_type=RESOURCES_MODELS_DIR_NAME, model=RETRAINING_MODEL_NAME)), 
        override_usb_camera=None, 
        override_video_input=str(Path(RESOURCES_ROOT_PATH_DEFAULT)/BARCODE_VIDEO_EXAMPLE_NAME),
        override_labels_json=str(get_resource_path(pipeline_name=None, resource_type=DEFAULT_LOCAL_RESOURCES_PATH, model=RETRAINING_BARCODE_LABELS_JSON_NAME))
    )
    log_file_path_empty = os.path.join(log_dir, "retraining.log")
    stdout, stderr = b"", b""
    cmd = ['python', '-u', "hailo_apps/hailo_app_python/apps/detection/detection_pipeline.py"] + args
    print(f"Running retraining command: {' '.join(cmd)}")
    stdout, stderr = run_pipeline_pythonpath_with_args("hailo_apps/hailo_app_python/apps/detection/detection_pipeline.py", args, log_file_path_empty)
    out_str = stdout.decode().lower() if stdout else ""
    err_str = stderr.decode().lower() if stderr else ""
    print(f"Retraining Output:\n{out_str}")
    assert "error" not in err_str, f"Reported an error in retraining run: {err_str}"
    assert "traceback" not in err_str, f"Traceback in retraining run: {err_str}"

if __name__ == "__main__":
    pytest.main(["-v", __file__])