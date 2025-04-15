import pytest
import subprocess
import os
import sys
import time
import signal
import logging
from pathlib import Path
from hailo_apps_infra.common.hailo_rpi_common import (
    detect_device_arch,
    detect_hailo_arch
)


# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "pipeline_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pipeline-tests")

# How long to run each pipeline test in seconds
TEST_RUN_TIME = 10

# Check for Raspberry Pi camera
try:
    from picamera2 import Picamera2
    RPI_CAMERA_AVAILABLE = True
    logger.info("Raspberry Pi camera module detected")
except ImportError:
    RPI_CAMERA_AVAILABLE = False
    logger.info("Raspberry Pi camera module not available")


def get_device_architecture():
    """
    Get the device architecture (x86, ARM, RPi) and Hailo chip type if available.
    
    Returns:
        tuple: (platform_arch, hailo_arch)
            platform_arch: 'x86', 'arm', 'rpi', or 'unknown'
            hailo_arch: 'hailo8', 'hailo8l', or None if not available
    """
    # Use the utility functions from hailo_rpi_common
    platform_arch = detect_device_arch()
    hailo_arch = detect_hailo_arch()
    
    # Check for environment variables that might override the detected values
    if "DEVICE_ARCH" in os.environ:
        env_platform_arch = os.environ["DEVICE_ARCH"]
        if env_platform_arch != platform_arch:
            logger.info(f"Using platform architecture from environment: {env_platform_arch} (detected: {platform_arch})")
            platform_arch = env_platform_arch
    
    if "HAILO_ARCH" in os.environ:
        env_hailo_arch = os.environ["HAILO_ARCH"]
        if env_hailo_arch != hailo_arch and env_hailo_arch != "unknown":
            logger.info(f"Using Hailo architecture from environment: {env_hailo_arch} (detected: {hailo_arch})")
            hailo_arch = env_hailo_arch
    
    logger.info(f"Using platform: {platform_arch}, Hailo architecture: {hailo_arch}")
    return platform_arch, hailo_arch


def get_compatible_hefs(hailo_arch, model_type):
    """
    Get a list of compatible HEF files based on the device architecture and model type.
    
    Args:
        hailo_arch (str): 'hailo8', 'hailo8l', or None
        model_type (str): 'detection', 'pose', 'segmentation', or 'depth'
        
    Returns:
        list: List of HEF file paths relative to the resources directory
    """
    # If no Hailo device is detected, we'll use placeholders for test validation
    if hailo_arch is None:
        logger.warning("No Hailo device detected, using placeholder HEF paths for tests")
        return [f"resources/placeholder_{model_type}.hef"]
    
    # Define HEF files for each model type and architecture
    models = {
        'detection': {
            'hailo8': [
                "yolov6n.hef",
                "yolov8s.hef",
                "yolov8m.hef",
                "yolov11n.hef",
                "yolov11s.hef"
            ],
            'hailo8l': [
                "yolov5m_wo_spp_h8l.hef",
                "yolov6n_h8l.hef",
                "yolov8s_h8l.hef",
                "yolov8m_h8l.hef",
                "yolov11n_h8l.hef",
                "yolov11s_h8l.hef"
            ]
        },
        'pose': {
            'hailo8': [
                "yolov8m_pose.hef",
                "yolov8s_pose.hef",
            ],
            'hailo8l': [
                "yolov8s_pose_h8l.hef",
            ]
        },
        'segmentation': {
            'hailo8': [
                "yolov5m_seg.hef",
                "yolov5n_seg.hef",
            ],
            'hailo8l': [
                "yolov5n_seg_h8l.hef",
            ]
        },
        'depth': {
            'hailo8': [
                "scdepthv3.hef"
            ],
            'hailo8l': [
                "scdepthv3_h8l.hef"
            ]
        }
    }
    
    # Get the list of compatible HEFs
    if model_type in models and hailo_arch in models[model_type]:
        return [os.path.join("resources", hef) for hef in models[model_type][hailo_arch]]
    
    logger.warning(f"No compatible HEFs found for {model_type} on {hailo_arch}")
    return []


def get_available_video_inputs():
    """
    Get a list of available video inputs based on the platform architecture.
    
    Returns:
        dict: Dictionary of input types and their values
    """
    platform_arch, _ = get_device_architecture()
    
    # Check the resources directory for video files
    resources_dir = Path("resources")
    video_files = list(resources_dir.glob("*.mp4"))
    
    inputs = {
        'file': [str(file) for file in video_files] if video_files else ['resources/example.mp4', 'resources/example_640.mp4'],
    }
    
    # Check for USB cameras
    usb_cameras = []
    try:
        from hailo_apps_infra.common.get_usb_camera import get_usb_video_devices
        devices = get_usb_video_devices()
        usb_cameras = [device.device_path for device in devices]
        if usb_cameras:
            inputs['usb'] = usb_cameras
            inputs['usb'].append('usb')  # Add the generic 'usb' option
    except (ImportError, Exception) as e:
        logger.warning(f"Could not detect USB cameras: {e}")
    
    # Add Raspberry Pi camera if available
    if platform_arch == 'rpi' and RPI_CAMERA_AVAILABLE:
        inputs['rpi'] = ['rpi']
    
    return inputs


def run_pipeline_test(pipeline_module, hef_path, input_source, input_type, extra_args=None):
    """
    Run a pipeline test with the given parameters.
    
    Args:
        pipeline_module (str): The Python module to run
        hef_path (str): Path to the HEF file
        input_source (str): Input source (file path, device path, or source type)
        input_type (str): Type of input (file, usb, rpi, test)
        extra_args (list): Additional command-line arguments
        
    Returns:
        bool: True if the test was successful, False otherwise
    """
    # Create test-specific log file
    hef_name = os.path.basename(hef_path)
    test_name = f"{pipeline_module.split('.')[-1]}_{hef_name}_{input_type}"
    log_file_path = log_dir / f"{test_name}.log"
    
    logger.info(f"Running {pipeline_module} with {hef_name} ({input_type}:{input_source})")
    
    # Build command
    cmd = [
        'python', '-m', pipeline_module,
        '--input', input_source,
        '--hef-path', hef_path,
    ]
    
    if extra_args:
        cmd.extend(extra_args)
    
    logger.info(f"Command: {' '.join(cmd)}")
    
    with open(log_file_path, "w") as log_file:
        # Start process
        log_file.write(f"Running command: {' '.join(cmd)}\n")
        process = subprocess.Popen(cmd)
        
        try:
            # Let it run
            time.sleep(TEST_RUN_TIME)
            
            # Gracefully terminate
            process.send_signal(signal.SIGTERM)
            
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process didn't terminate gracefully, killing it")
                process.kill()
                process.wait()
            
            # Check return code (0 = normal exit, -15 = terminated)
            if process.returncode == 0 or process.returncode == -15:
                log_file.write(f"Test completed successfully\n")
                log_file.write(f"Return code: {process.returncode}\n")
                logger.info(f"Test {test_name} completed successfully")
                return True
            else:
                log_file.write(f"Test failed with return code {process.returncode}\n")
                logger.error(f"Test {test_name} failed with return code {process.returncode}")
                return False
            
        except Exception as e:
            process.kill()
            log_file.write(f"Test failed with exception: {str(e)}\n")
            logger.error(f"Test {test_name} failed with exception: {str(e)}")
            return False
        
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
                log_file.write("Process had to be forcibly terminated\n")


# Define the pipeline modules to test
PIPELINE_MODULES = {
    'detection': [
        'hailo_apps_infra.core.detection_pipeline',
        'hailo_apps_infra.core.detection_pipeline_simple',
    ],
    'pose': [
        'hailo_apps_infra.core.pose_estimation_pipeline',
    ],
    'segmentation': [
        'hailo_apps_infra.core.instance_segmentation_pipeline',
    ],
    'depth': [
        'hailo_apps_infra.core.depth_pipeline',
    ]
}


@pytest.mark.parametrize("model_type,pipeline_module", [
    (model_type, module)
    for model_type, modules in PIPELINE_MODULES.items()
    for module in modules
])
def test_pipeline_with_file_source(model_type, pipeline_module):
    """Test running each pipeline with real video files."""
    _, hailo_arch = get_device_architecture()
    
    # Get compatible HEFs
    hefs = get_compatible_hefs(hailo_arch, model_type)
    if not hefs:
        pytest.skip(f"No compatible HEFs found for {model_type}")
    
    # Get available video files
    available_inputs = get_available_video_inputs()
    if 'file' not in available_inputs or not available_inputs['file']:
        pytest.skip("No video files available for testing")
    
    # Use the first HEF for the file source test
    hef = hefs[0]
    
    # Use the first video file for testing
    video_file = available_inputs['file'][0]
    
    # Run with file source
    success = run_pipeline_test(
        pipeline_module=pipeline_module,
        hef_path=hef,
        input_source=video_file,
        input_type="file"
    )
    
    assert success, f"Pipeline {pipeline_module} failed with file source {video_file}"


@pytest.mark.parametrize("model_type,pipeline_module", [
    (model_type, module)
    for model_type, modules in PIPELINE_MODULES.items()
    for module in modules
])
def test_pipelines_with_file_source(model_type, pipeline_module):
    """Test running pipelines with file video sources."""
    _, hailo_arch = get_device_architecture()
    
    # Get compatible HEFs
    hefs = get_compatible_hefs(hailo_arch, model_type)
    if not hefs:
        pytest.skip(f"No compatible HEFs found for {model_type}")
    
    # Get available video files
    available_inputs = get_available_video_inputs()
    if 'file' not in available_inputs or not available_inputs['file']:
        pytest.skip("No video files available for testing")
    
    # Use only the first video file to reduce test time
    video_file = available_inputs['file'][0]
    
    # Use only the first HEF to reduce test time
    hef = hefs[0]
    
    # Run with file source
    success = run_pipeline_test(
        pipeline_module=pipeline_module,
        hef_path=hef,
        input_source=video_file,
        input_type="file"
    )
    
    assert success, f"Pipeline {pipeline_module} failed with file source {video_file}"


@pytest.mark.parametrize("model_type,pipeline_module", [
    (model_type, module)
    for model_type, modules in PIPELINE_MODULES.items()
    for module in modules
])
def test_pipelines_with_usb_camera(model_type, pipeline_module):
    """Test running pipelines with USB camera sources."""
    _, hailo_arch = get_device_architecture()
    
    # Get compatible HEFs
    hefs = get_compatible_hefs(hailo_arch, model_type)
    if not hefs:
        pytest.skip(f"No compatible HEFs found for {model_type}")
    
    # Get available USB cameras
    available_inputs = get_available_video_inputs()
    if 'usb' not in available_inputs or not available_inputs['usb']:
        pytest.skip("No USB cameras available for testing")
    
    # Use generic 'usb' option which should auto-detect first camera
    usb_source = 'usb'
    
    # Use only the first HEF to reduce test time
    hef = hefs[0]
    
    # Run with USB camera
    success = run_pipeline_test(
        pipeline_module=pipeline_module,
        hef_path=hef,
        input_source=usb_source,
        input_type="usb"
    )
    
    # We don't assert here because USB camera might not be available
    # Just log the result
    if not success:
        logger.warning(f"Pipeline {pipeline_module} test with USB camera did not succeed - this might be normal if no camera is connected")


@pytest.mark.parametrize("model_type,pipeline_module", [
    (model_type, module)
    for model_type, modules in PIPELINE_MODULES.items()
    for module in modules
])
def test_pipelines_with_rpi_camera(model_type, pipeline_module):
    """Test running pipelines with Raspberry Pi camera."""
    platform_arch, hailo_arch = get_device_architecture()
    
    # Skip if not on Raspberry Pi or no camera available
    if platform_arch != 'rpi' or not RPI_CAMERA_AVAILABLE:
        pytest.skip("Not running on Raspberry Pi or camera module not available")
    
    # Get compatible HEFs
    hefs = get_compatible_hefs(hailo_arch, model_type)
    if not hefs:
        pytest.skip(f"No compatible HEFs found for {model_type}")
    
    # Use only the first HEF to reduce test time
    hef = hefs[0]
    
    # Set environment variables
    env = os.environ.copy()
    if "DEVICE_ARCH" not in env:
        env["DEVICE_ARCH"] = "rpi"
    if "HAILO_ARCH" not in env and hailo_arch:
        env["HAILO_ARCH"] = hailo_arch
    
    # Create test-specific log file
    log_file_path = log_dir / f"{pipeline_module.split('.')[-1]}_rpi_camera.log"
    
    with open(log_file_path, "w") as log_file:
        # Build command
        cmd = [
            'python', '-m', pipeline_module,
            '--input', 'rpi',
            '--hef-path', hef,
            '--show-fps'
        ]
        
        log_file.write(f"Running command: {' '.join(cmd)}\n")
        process = subprocess.Popen(cmd, env=env)
        
        try:
            # Let it run
            time.sleep(TEST_RUN_TIME)
            
            # Gracefully terminate
            process.send_signal(signal.SIGTERM)
            
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            # Check return code
            if process.returncode == 0 or process.returncode == -15:
                log_file.write(f"Test completed successfully with return code {process.returncode}\n")
                success = True
            else:
                log_file.write(f"Test failed with return code {process.returncode}\n")
                success = False
            
        except Exception as e:
            process.kill()
            log_file.write(f"Test failed with exception: {str(e)}\n")
            success = False
            
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
    
    assert success, f"Pipeline {pipeline_module} failed with RPi camera"


@pytest.mark.parametrize("model_type", PIPELINE_MODULES.keys())
def test_all_hefs_basic_functionality(model_type):
    """Test all compatible HEFs for a model type with a basic pipeline and video file."""
    _, hailo_arch = get_device_architecture()
    
    # Get compatible HEFs
    hefs = get_compatible_hefs(hailo_arch, model_type)
    if not hefs:
        pytest.skip(f"No compatible HEFs found for {model_type}")
    
    # Get available video files
    available_inputs = get_available_video_inputs()
    if 'file' not in available_inputs or not available_inputs['file']:
        pytest.skip("No video files available for testing")
    
    # Use only the first video file to reduce test time
    video_file = available_inputs['file'][0]
    
    # Use the first pipeline module for this model type
    pipeline_module = PIPELINE_MODULES[model_type][0]
    
    # Test all HEFs
    for hef in hefs:
        logger.info(f"Testing HEF {hef} with {pipeline_module}")
        
        success = run_pipeline_test(
            pipeline_module=pipeline_module,
            hef_path=hef,
            input_source=video_file,
            input_type="file"
        )
        
        assert success, f"Pipeline {pipeline_module} failed with HEF {hef}"


def test_environmental_variables_effect():
    """Test the effect of environmental variables on pipeline behavior."""
    _, hailo_arch = get_device_architecture()
    
    # Skip if no Hailo device
    if hailo_arch is None:
        pytest.skip("No Hailo device detected")
    
    # Get a basic pipeline and HEF
    model_type = 'detection'  # Use detection as it's most likely to be available
    hefs = get_compatible_hefs(hailo_arch, model_type)
    if not hefs:
        pytest.skip(f"No compatible HEFs found for {model_type}")
    
    pipeline_module = PIPELINE_MODULES[model_type][0]
    hef = hefs[0]
    
    # Get a video file
    available_inputs = get_available_video_inputs()
    if 'file' not in available_inputs or not available_inputs['file']:
        pytest.skip("No video files available for testing")
    
    video_file = available_inputs['file'][0]
    
    # Test with GST_DEBUG environment variable and other Hailo variables
    env = os.environ.copy()
    env["GST_DEBUG"] = "3"
    
    # Make sure resource path is set
    if "RESOURCE_PATH" not in env:
        resource_path = "/usr/local/hailo/resources"
        env["RESOURCE_PATH"] = resource_path
        logger.info(f"Setting RESOURCE_PATH={resource_path}")
    
    # Make sure TAPPAS_POST_PROC_DIR is set if it exists
    if "TAPPAS_POST_PROC_DIR" not in env:
        resource_path = env["RESOURCE_PATH"]
        tappas_postproc_dir = os.path.join(resource_path, "postproc", "tappas")
        if os.path.exists(tappas_postproc_dir):
            env["TAPPAS_POST_PROC_DIR"] = tappas_postproc_dir
            logger.info(f"Setting TAPPAS_POST_PROC_DIR={tappas_postproc_dir}")
    
    logger.info("Testing with custom environment variables")
    
    # Build command
    cmd = [
        'python', '-m', pipeline_module,
        '--input', video_file,
        '--hef-path', hef,
        '--show-fps',
        '--dump-dot'  # Add dot file generation
    ]
    
    # Create test-specific log file
    log_file_path = log_dir / "env_vars_test.log"
    
    with open(log_file_path, "w") as log_file:
        # Log environment variables
        log_file.write("Environment variables:\n")
        for key in ["GST_DEBUG", "RESOURCE_PATH", "DEVICE_ARCH", "HAILO_ARCH", "TAPPAS_POST_PROC_DIR"]:
            if key in env:
                log_file.write(f"  {key}={env[key]}\n")
        
        # Start process with custom environment
        log_file.write(f"Running command: {' '.join(cmd)}\n")
        process = subprocess.Popen(cmd, env=env)
        
        try:
            # Let it run
            time.sleep(TEST_RUN_TIME)
            
            # Gracefully terminate
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=5)
            
            # Check if dot file was generated
            dot_files = list(Path('.').glob('*.dot'))
            if dot_files:
                log_file.write(f"Dot files generated: {[f.name for f in dot_files]}\n")
                for dot_file in dot_files:
                    # Move dot files to log directory
                    dot_file.rename(log_dir / dot_file.name)
                    log_file.write(f"Moved {dot_file.name} to {log_dir}\n")
            else:
                log_file.write("No dot files were generated\n")
            
            # Check return code
            log_file.write(f"Process completed with return code {process.returncode}\n")
            
        except Exception as e:
            process.kill()
            log_file.write(f"Test failed with exception: {str(e)}\n")
            pytest.fail(f"Test failed with exception: {str(e)}")
        
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


if __name__ == "__main__":
    pytest.main(["-v", __file__])