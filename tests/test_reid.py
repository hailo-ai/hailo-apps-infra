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
    check_hailo8l_on_hailo8_warning,
    check_qos_performance_warning,
)
from hailo_apps.hailo_app_python.core.common.installation_utils import detect_hailo_arch
from hailo_apps.hailo_app_python.core.common.defines import HAILO8_ARCH, HAILO8L_ARCH, RESOURCES_ROOT_PATH_DEFAULT
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
        "name": "reid_multisource",
        "module": "hailo_apps.hailo_app_python.apps.reid_multisource.reid_multisource_pipeline",
        "script": "hailo_apps/hailo_app_python/apps/reid_multisource/reid_multisource_pipeline.py",
        "cli": "hailo-reid"
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

@pytest.mark.parametrize('run_method_name', list(run_methods.keys()))
def test_train_multiscale(pipeline, run_method_name):
    test_name = 'test_reid'
    args = get_pipeline_args(suite='sources')
    run_test(pipeline, run_method_name, test_name, args)


def run_hailo8l_model_on_hailo8_reid(model_name, extra_args=None):
    """Helper function to run a Hailo8L model on Hailo 8 architecture for REID pipeline.
    
    Args:
        model_name: Name of the Hailo8L model to run
        extra_args: Additional arguments to pass to the pipeline
    
    Returns:
        tuple: (stdout, stderr, success)
    """
    hailo_arch = detect_hailo_arch()
    if hailo_arch != HAILO8_ARCH:
        logger.warning(f"Not running on Hailo 8 architecture (current: {hailo_arch})")
        return b"", b"", False

    # Create logs directory
    log_dir = "logs/h8l_on_h8_reid_tests"
    os.makedirs(log_dir, exist_ok=True)

    # Build full HEF path for Hailo8L model
    hef_full_path = os.path.join(RESOURCES_ROOT_PATH_DEFAULT, "models", HAILO8L_ARCH, f"{model_name}.hef")
    
    # Prepare CLI arguments
    args = ["--hef-path", hef_full_path]
    if extra_args:
        args.extend(extra_args)

    # Create log file path
    log_file_path = os.path.join(log_dir, f"reid_{model_name}.log")

    try:
        logger.info(f"Testing REID with Hailo8L model: {model_name} on Hailo 8")
        stdout, stderr = run_pipeline_cli_with_args("hailo-reid", args, log_file_path)

        # Check for errors
        err_str = stderr.decode().lower() if stderr else ""
        success = "error" not in err_str and "traceback" not in err_str
        
        # Check for HailoRT warning (expected for Hailo8L on Hailo8)
        has_warning = check_hailo8l_on_hailo8_warning(stdout, stderr)
        if not has_warning:
            logger.warning(f"Expected HailoRT warning not found for {model_name} on Hailo 8")
        
        # Check for QoS performance issues
        has_qos_warning, qos_count = check_qos_performance_warning(stdout, stderr)
        if has_qos_warning:
            logger.warning(f"Performance issue detected: QoS messages: {qos_count} total (>=100) for {model_name}")
        
        return stdout, stderr, success

    except Exception as e:
        logger.error(f"Exception while testing {model_name} on Hailo 8: {e}")
        return b"", str(e).encode(), False


def test_hailo8l_models_on_hailo8_reid():
    """Test Hailo8L models on Hailo 8 for REID pipeline."""
    hailo_arch = detect_hailo_arch()
    if hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {hailo_arch}")

    # Define Hailo8L models that can be used with REID
    h8l_models = ["yolov5m_wo_spp", "yolov6n", "yolov8s", "yolov8m", "yolov11n", "yolov11s"]
    
    logger.info(f"Running Hailo8L model test on Hailo 8 for REID pipeline")
    
    failed_models = []
    
    for model in h8l_models:
        stdout, stderr, success = run_hailo8l_model_on_hailo8_reid(model)
        
        # Check for QoS performance issues
        has_qos_warning, qos_count = check_qos_performance_warning(stdout, stderr)
        if has_qos_warning:
            logger.warning(f"Performance issue detected: QoS messages: {qos_count} total (>=100) for {model}")
        
        if not success:
            failed_models.append({
                "model": model,
                "stderr": stderr.decode() if stderr else "",
                "stdout": stdout.decode() if stdout else "",
            })
            logger.error(f"Failed to run {model} with REID")
        else:
            logger.info(f"Successfully ran {model} with REID")

    # Assert that all models passed
    if failed_models:
        failure_details = "\n".join(
            [f"Model: {fail['model']}\nError: {fail['stderr']}\n" for fail in failed_models]
        )
        pytest.fail(f"Failed Hailo8L models for REID:\n{failure_details}")


if __name__ == "__main__":
    pytest.main(["-v", __file__])