# region imports
# Standard library imports
import os
import logging

# Third-party imports
import pytest

# Local application-specific imports
from hailo_apps.hailo_app_python.core.common.test_utils import (
    run_pipeline_module_with_args,
    run_pipeline_pythonpath_with_args,
    run_pipeline_cli_with_args,
    get_pipeline_args,
    check_qos_performance_warning,
)
# endregion imports

# Configure logging as needed.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_run_everything')
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Define pipeline configurations.
@pytest.fixture
def pipeline():
    return {
        "name": "tiling",
        "module": "hailo_apps.hailo_app_python.apps.tiling.tiling_pipeline",
        "script": "hailo_apps/hailo_app_python/apps/tiling/tiling_pipeline.py",
        "cli": "hailo-tiling"
    }

# Map each run method label to its corresponding function.
run_methods = {
    'module': run_pipeline_module_with_args,
    'pythonpath': run_pipeline_pythonpath_with_args,
    'cli': run_pipeline_cli_with_args
}

def run_test(pipeline, run_method_name, test_name, args):
    """
    Helper function to run the test logic.
    """
    log_file_path = os.path.join(log_dir, f"{pipeline['name']}_{test_name}_{run_method_name}.log")

    if run_method_name == 'module':
        stdout, stderr = run_methods[run_method_name](pipeline['module'], args, log_file_path)
    elif run_method_name == 'pythonpath':
        stdout, stderr = run_methods[run_method_name](pipeline['script'], args, log_file_path)
    elif run_method_name == 'cli':
        stdout, stderr = run_methods[run_method_name](pipeline['cli'], args, log_file_path)
    else:
        pytest.fail(f"Unknown run method: {run_method_name}")

    out_str = stdout.decode().lower() if stdout else ""
    err_str = stderr.decode().lower() if stderr else ""
    print(f"Completed: {test_name}, {pipeline['name']}, {run_method_name}: {out_str}")
    assert 'error' not in err_str, f"{pipeline['name']} ({run_method_name}) reported an error in {test_name}: {err_str}"
    assert 'traceback' not in err_str, f"{pipeline['name']} ({run_method_name}) traceback in {test_name} : {err_str}"
    # Check for QoS performance issues
    has_qos_warning, qos_count = check_qos_performance_warning(stdout, stderr)
    if has_qos_warning:
        logger.warning(f"Performance issue detected: QoS messages: {qos_count} total (>=100) for {pipeline['name']} ({run_method_name}) {test_name}")


# Tests based on README.md examples

@pytest.mark.parametrize('run_method_name', list(run_methods.keys()))
def test_default_visdrone_detection(pipeline, run_method_name):
    """Test default VisDrone aerial detection mode from README example."""
    test_name = 'test_default_visdrone_detection'
    args = []  # Default behavior - uses VisDrone MobileNetSSD + VisDrone video
    run_test(pipeline, run_method_name, test_name, args)


@pytest.mark.parametrize('run_method_name', list(run_methods.keys()))
def test_general_detection_mode(pipeline, run_method_name):
    """Test general detection mode from README example."""
    test_name = 'test_general_detection_mode'
    args = ['--general-detection']  # Uses YOLO + COCO dataset + multi-scale
    run_test(pipeline, run_method_name, test_name, args)


@pytest.mark.parametrize('run_method_name', list(run_methods.keys()))
def test_live_camera_general_detection(pipeline, run_method_name):
    """Test live camera with general detection from README example."""
    test_name = 'test_live_camera_general_detection'
    # Get proper USB camera arguments using the same method as test_all_pipelines.py
    usb_args = get_pipeline_args(suite="usb_camera")
    args = usb_args + ['--general-detection']  # Uses YOLO + COCO dataset + multi-scale
    run_test(pipeline, run_method_name, test_name, args)


if __name__ == "__main__":
    pytest.main(["-v", __file__])