import os
import pytest
import logging
from pathlib import Path


from hailo_apps.hailo_app_python.core.common.test_utils import (
    run_pipeline_module_with_args,
    run_pipeline_pythonpath_with_args,
    run_pipeline_cli_with_args,
    get_pipeline_args,
)

# Import installation utilities
from hailo_apps.hailo_app_python.core.common.installation_utils import detect_hailo_arch, detect_host_arch
from hailo_apps.hailo_app_python.core.common.camera_utils import is_rpi_camera_available

from hailo_apps.hailo_app_python.core.common.defines import (
    HAILO8_ARCH,
    HAILO8L_ARCH,
)

from hailo_apps.hailo_app_python.core.common.test_utils import run_pipeline_pythonpath_with_args, get_pipeline_args
from hailo_apps.hailo_app_python.core.common.core import get_resource_path
from hailo_apps.hailo_app_python.core.common.defines import RETRAINING_MODEL_NAME, RESOURCES_MODELS_DIR_NAME, BARCODE_VIDEO_EXAMPLE_NAME, RESOURCES_ROOT_PATH_DEFAULT, RESOURCES_JSON_DIR_NAME, RETRAINING_BARCODE_LABELS_JSON_NAME


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

h8_hefs_detection = [
    "yolov5m_wo_spp.hef",
    "yolov6n.hef",
    "yolov8s.hef",
    "yolov8m.hef",
    "yolov11n.hef",
    "yolov11s.hef"
]

h8l_hefs_detection = [
    "yolov5m_wo_spp.hef",
    "yolov6n.hef",
    "yolov8s.hef",
    "yolov8m.hef",
    "yolov11n.hef",
    "yolov11s.hef"
]

h8_hefs_pose_estimation = [
    "yolov8s_pose.hef",
    "yolov8m_pose.hef",
]

h8l_hefs_pose_estimation = [
    "yolov8s_pose.hef",
]

h8l_hefs_segmentation = [
    "yolov5m_seg.hef",
    "yolov5n_seg.hef",
]

h8_hefs_segmentation = [
    "yolov5n_seg.hef",
]

# HEF configurations mapping pipeline types to their HEF lists
HEF_CONFIG = {
    HAILO8_ARCH: {
        "detection": h8_hefs_detection,
        "pose_estimation": h8_hefs_pose_estimation,
        "segmentation": h8_hefs_segmentation,
    },
    HAILO8L_ARCH: {
        "detection": h8l_hefs_detection,
        "pose_estimation": h8l_hefs_pose_estimation,
        "segmentation": h8l_hefs_segmentation,
    }
}

# Pipeline to CLI mapping
PIPELINE_CLI_MAP = {
    "detection": "hailo-detect",
    "pose_estimation": "hailo-pose",
    "segmentation": "hailo-seg",
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


def run_hef_with_pipeline(pipeline_type, hef_file, extra_args=None, hailo_arch=None):
    """
    Helper function to run a specific HEF with a pipeline.
    """
    cli_command = PIPELINE_CLI_MAP.get(pipeline_type)
    if not cli_command:
        logger.error(f"Unknown pipeline type: {pipeline_type}")
        return b"", b"", False

    # Determine architecture if not provided
    if hailo_arch is None:
        hailo_arch = detect_hailo_arch()

    # Create logs directory
    log_dir = "logs/hef_tests"
    os.makedirs(log_dir, exist_ok=True)

    # Build full HEF path
    resources_root = RESOURCES_ROOT_PATH_DEFAULT
    hef_full_path = os.path.join(resources_root, "models", hailo_arch, hef_file)

    # Prepare CLI arguments
    args = ["--hef-path", hef_full_path]
    if extra_args:
        args.extend(extra_args)

    # Create log file path
    log_file_path = os.path.join(log_dir, f"{pipeline_type}_{hef_file.replace('.hef', '')}.log")

    try:
        logger.info(f"Testing {pipeline_type} with HEF: {hef_file}")
        stdout, stderr = run_pipeline_cli_with_args(cli_command, args, log_file_path)

        # Check for errors
        err_str = stderr.decode().lower() if stderr else ""
        success = "error" not in err_str and "traceback" not in err_str
        return stdout, stderr, success

    except Exception as e:
        logger.error(f"Exception while testing {hef_file}: {e}")
        return b"", str(e).encode(), False



@pytest.mark.parametrize("pipeline_type", ["detection", "pose_estimation", "segmentation"])
def test_all_hefs_by_pipeline(pipeline_type):
    """
    Test all HEFs for a specific pipeline type.
    This creates separate test cases for each pipeline type.
    """
    # Detect the architecture of the Hailo device
    hailo_arch = detect_hailo_arch()
    
    if hailo_arch not in HEF_CONFIG:
        pytest.skip(f"Unsupported Hailo architecture: {hailo_arch}")
    
    # Get HEFs for the current architecture and pipeline type
    hef_list = HEF_CONFIG[hailo_arch].get(pipeline_type, [])
    
    if not hef_list:
        pytest.skip(f"No HEFs configured for {pipeline_type} on {hailo_arch}")
    
    logger.info(f"Testing {len(hef_list)} HEFs for {pipeline_type} on {hailo_arch}")
    
    # Test each HEF individually
    failed_hefs = []
    for hef in hef_list:
        stdout, stderr, success = run_hef_with_pipeline(pipeline_type, hef)
        
        if not success:
            failed_hefs.append({
                'hef': hef,
                'stderr': stderr.decode() if stderr else "",
                'stdout': stdout.decode() if stdout else ""
            })
            logger.error(f"Failed to run {hef} with {pipeline_type}")
        else:
            logger.info(f"Successfully ran {hef} with {pipeline_type}")
    
    # Assert that all HEFs passed
    if failed_hefs:
        failure_details = "\n".join([
            f"HEF: {fail['hef']}\nError: {fail['stderr']}\n" 
            for fail in failed_hefs
        ])
        pytest.fail(f"Failed HEFs for {pipeline_type}:\n{failure_details}")


def test_all_hefs_comprehensive():
    """
    Comprehensive test that runs all HEFs for all supported pipeline types.
    This is a single test that gives you an overview of all HEF testing.
    """
    # Detect the architecture of the Hailo device
    hailo_arch = detect_hailo_arch()
    
    if hailo_arch not in HEF_CONFIG:
        pytest.skip(f"Unsupported Hailo architecture: {hailo_arch}")
    
    logger.info(f"Running comprehensive HEF test for {hailo_arch}")
    
    all_results = {}
    total_tests = 0
    total_passed = 0
    
    # Test each pipeline type
    for pipeline_type, hef_list in HEF_CONFIG[hailo_arch].items():
        if not hef_list:
            continue
            
        logger.info(f"Testing {pipeline_type} pipeline with {len(hef_list)} HEFs")
        all_results[pipeline_type] = {}
        
        for hef in hef_list:
            total_tests += 1
            stdout, stderr, success = run_hef_with_pipeline(pipeline_type, hef)
            
            all_results[pipeline_type][hef] = {
                'success': success,
                'stdout': stdout.decode() if stdout else "",
                'stderr': stderr.decode() if stderr else ""
            }
            
            if success:
                total_passed += 1
                logger.info(f"✓ {pipeline_type}: {hef}")
            else:
                logger.error(f"✗ {pipeline_type}: {hef}")
    
    # Generate summary report
    logger.info(f"\nHEF Test Summary:")
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Passed: {total_passed}")
    logger.info(f"Failed: {total_tests - total_passed}")
    
    # Log detailed results
    for pipeline_type, results in all_results.items():
        failed_hefs = [hef for hef, result in results.items() if not result['success']]
        if failed_hefs:
            logger.error(f"{pipeline_type} failed HEFs: {failed_hefs}")
    
    # Assert overall success
    if total_passed < total_tests:
        failed_details = []
        for pipeline_type, results in all_results.items():
            for hef, result in results.items():
                if not result['success']:
                    failed_details.append(f"{pipeline_type}/{hef}: {result['stderr']}")
        
        failure_summary = "\n".join(failed_details)
        pytest.fail(f"HEF testing failed. {total_passed}/{total_tests} tests passed.\n\nFailures:\n{failure_summary}")


def test_retraining_defaults():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # build each path component-wise
    hef_path = str(
        Path(RESOURCES_ROOT_PATH_DEFAULT)
        / "models"
        / "hailo8l"
        / "yolov8s-hailo8l-barcode.hef"
    )
    video_input = str(
        Path(RESOURCES_ROOT_PATH_DEFAULT)
        / "videos"
        / BARCODE_VIDEO_EXAMPLE_NAME
    )
    labels_json = str(
        get_resource_path(
            pipeline_name=None,
            resource_type=RESOURCES_JSON_DIR_NAME,
            model=RETRAINING_BARCODE_LABELS_JSON_NAME
        )
    )

    args = get_pipeline_args(
        suite="labels,video_file,hef_path",
        hef_path=hef_path,
        override_usb_camera=None,
        override_video_input=video_input,
        override_labels_json=labels_json,
    )

    log_file = os.path.join(log_dir, "retraining.log")
    print(f"Running retraining with args: {args}")
    stdout, stderr = run_pipeline_pythonpath_with_args(
        "hailo_apps/hailo_app_python/apps/detection/detection_pipeline.py",
        args,
        log_file
    )

    out_str = stdout.decode().lower() if stdout else ""
    err_str = stderr.decode().lower() if stderr else ""
    print(f"Retraining stdout:\n{out_str}")

    assert "error" not in err_str,     f"Reported an error in retraining run: {err_str}"
    assert "traceback" not in err_str, f"Traceback in retraining run: {err_str}"

def test_hailo8l_models_on_hailo8():
    hailo_arch = detect_hailo_arch()
    if hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {hailo_arch}")

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # For each Hailo-8L detection HEF, try running it on the Hailo-8
    for hef in HEF_CONFIG[HAILO8L_ARCH]["detection"]:
        cli_cmd = PIPELINE_CLI_MAP["detection"]
        hef_path = os.path.join(RESOURCES_ROOT_PATH_DEFAULT, "models", HAILO8L_ARCH, hef)
        args = ["--hef-path", hef_path]
        log_file = os.path.join(log_dir, f"h8l_on_h8_{hef.replace('.hef','')}.log")

        stdout, stderr = run_pipeline_cli_with_args(cli_cmd, args, log_file)
        err_str = stderr.decode().lower() if stderr else ""

        assert "error" not in err_str,      f"{hef} raised an error: {err_str}"
        assert "traceback" not in err_str,  f"{hef} had a traceback: {err_str}"

if __name__ == "__main__":
    # You can run specific tests like this:
    # pytest test_file.py::test_all_hefs_by_pipeline -v
    # pytest test_file.py::test_all_hefs_comprehensive -v
    pytest.main(["-v", __file__])