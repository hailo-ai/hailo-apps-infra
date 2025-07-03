import os
import pytest
import logging
from hailo_apps.hailo_app_python.core.common.test_utils import run_pipeline_pythonpath_with_args, get_pipeline_args

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_run_everything")
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "hef_tests.log")

params = [
    {"pipeline": "detection/detection_pipeline",             "arch": "hailo8",  "hef": "yolov8m"},
    {"pipeline": "detection/detection_pipeline",             "arch": "hailo8l", "hef": "yolov8s_h8l"},

    # {"pipeline": "detection/detection_pipeline_simple",      "arch": "hailo8",  "hef": "yolov8m"},
    # {"pipeline": "detection/detection_pipeline_simple",      "arch": "hailo8l", "hef": "yolov8l"},

    # {"pipeline": "detection/depth_pipeline",                 "arch": "hailo8",  "hef": "yolov8m"},
    # {"pipeline": "detection/depth_pipeline",                 "arch": "hailo8l", "hef": "yolov8l"},

    # {"pipeline": "detection/instance_segmentation_pipeline", "arch": "hailo8",  "hef": "yolov8m"},
    # {"pipeline": "detection/instance_segmentation_pipeline", "arch": "hailo8l", "hef": "yolov8l"},

    # {"pipeline": "detection/pose_estimation_pipeline",       "arch": "hailo8",  "hef": "yolov8m"},
    # {"pipeline": "detection/pose_estimation_pipeline",       "arch": "hailo8l", "hef": "yolov8l"}
]

@pytest.mark.parametrize("params", params)
def test_hef(params):
    args = get_pipeline_args(suite="hef_path", hef_path=f"/usr/local/hailo/resources/models/{params['arch']}/{params['hef']}.hef")
    stdout, stderr = b"", b""
    stdout, stderr = run_pipeline_pythonpath_with_args("../hailo_apps/hailo_app_python/apps/detection/detection_pipeline.py", args, log_file_path)
    err_str = stderr.decode().lower() if stderr else ""
    assert "error" not in err_str, f"Error: {params['arch']} app {params['pipeline']} with hef {params['hef']}: {err_str}"
    assert "traceback" not in err_str, f"Traceback: {params['arch']} app {params['pipeline']} with hef {params['hef']}: {err_str}"
    assert "frame" in stdout.decode().lower(), f"No frames: {params['arch']} app {params['pipeline']} with hef {params['hef']}"
    assert "detection" in stdout.decode().lower(), f"No detections: {params['arch']} app {params['pipeline']} with hef {params['hef']}"

if __name__ == "__main__":
    pytest.main(["-v", __file__])