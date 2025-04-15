import pytest
import subprocess
import os
import sys
import time
import logging
import signal
from pathlib import Path
from hailo_apps_infra.common.hailo_rpi_common import (
    detect_device_arch,
    detect_hailo_arch,
    detect_pkg_installed
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("special-feature-tests")

# Create log directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# ---------------------------------------------------------
# Environment Variable Tests
# ---------------------------------------------------------

def test_env_variables_update():
    """Test that environment variables can be updated and affect application behavior."""
    # Get the current architecture and Hailo type
    device_arch = detect_device_arch()
    hailo_arch = detect_hailo_arch()
    
    # Skip test if no Hailo device
    if hailo_arch is None:
        pytest.skip("No Hailo device detected")
    
    # Create a temporary .env file with test values
    env_file = Path(".env.test")
    with open(env_file, "w") as f:
        f.write(f"DEVICE_ARCH={device_arch}\n")
        f.write(f"HAILO_ARCH={hailo_arch}\n")
        f.write("TEST_VARIABLE=test_value\n")
        f.write("GST_DEBUG=3\n")
    
    try:
        # Run a simple command to source the env file and check variables
        result = subprocess.run(
            ["bash", "-c", f"source {env_file} && env | grep -E 'DEVICE_ARCH|HAILO_ARCH|TEST_VARIABLE|GST_DEBUG'"],
            capture_output=True, text=True
        )
        
        # Check the output
        assert "DEVICE_ARCH" in result.stdout, "DEVICE_ARCH not found in environment"
        assert "HAILO_ARCH" in result.stdout, "HAILO_ARCH not found in environment"
        assert "TEST_VARIABLE=test_value" in result.stdout, "TEST_VARIABLE not found in environment"
        assert "GST_DEBUG=3" in result.stdout, "GST_DEBUG not found in environment"
        
        logger.info(f"Environment variables correctly set from test file:\n{result.stdout}")
    
    finally:
        # Clean up the test file
        env_file.unlink(missing_ok=True)


# ---------------------------------------------------------
# C++ Library Tests
# ---------------------------------------------------------

def test_cpp_libraries_loadable():
    """Test that the C++ libraries can be loaded by Python."""
    # List of libraries to test
    libraries = [
        'libdepth_postprocess.so',
        'libyolo_hailortpp_postprocess.so',
        'libyolov5seg_postprocess.so',
        'libyolov8pose_postprocess.so'
    ]
    
    # Check in resources directory
    resources_dir = Path("resources")
    for lib in libraries:
        lib_path = resources_dir / lib
        if lib_path.exists():
            # Try to load the library using ctypes
            try:
                import ctypes
                ctypes.CDLL(str(lib_path))
                logger.info(f"Successfully loaded {lib}")
            except Exception as e:
                logger.error(f"Failed to load {lib}: {e}")
                pytest.fail(f"Failed to load {lib}: {e}")
        else:
            logger.warning(f"Library {lib} not found in resources directory")


# ---------------------------------------------------------
# Pipeline Feature Tests
# ---------------------------------------------------------

def test_pipeline_termination_handling():
    """Test that pipelines handle termination signals correctly."""
    # Get device architecture
    _, hailo_arch = detect_device_arch(), detect_hailo_arch()
    
    # Skip if no Hailo device
    if hailo_arch is None:
        pytest.skip("No Hailo device detected")
    
    # Get a test video file
    resources_dir = Path("resources")
    video_files = list(resources_dir.glob("*.mp4"))
    if not video_files:
        pytest.skip("No video files available for testing")
    
    video_file = str(video_files[0])
    
    # Basic detection pipeline
    pipeline_module = "hailo_apps_infra.core.detection_pipeline"
    
    # Find a HEF file
    hef_files = list(resources_dir.glob("*.hef"))
    if not hef_files:
        pytest.skip("No HEF files available for testing")
    
    hef_file = str(hef_files[0])
    
    # Create test log file
    log_file_path = log_dir / "termination_test.log"
    
    with open(log_file_path, "w") as log_file:
        # Start the pipeline process
        cmd = [
            'python', '-m', pipeline_module,
            '--input', video_file,
            '--hef-path', hef_file,
            '--show-fps'
        ]
        
        log_file.write(f"Starting command: {' '.join(cmd)}\n")
        process = subprocess.Popen(cmd)
        
        try:
            # Let it run for a few seconds
            time.sleep(3)
            
            # Send signals and verify handling
            # First try SIGINT (Ctrl+C)
            log_file.write("Sending SIGINT\n")
            process.send_signal(signal.SIGINT)
            
            try:
                # Wait a short time for the process to handle the signal
                process.wait(timeout=5)
                log_file.write(f"Process exited with return code {process.returncode} after SIGINT\n")
                
                # If we get here, the process handled SIGINT correctly
                assert process.returncode in [0, -2], f"Process returned unexpected code {process.returncode} after SIGINT"
            
            except subprocess.TimeoutExpired:
                # Process didn't handle SIGINT, try SIGTERM
                log_file.write("Process didn't respond to SIGINT, trying SIGTERM\n")
                process.send_signal(signal.SIGTERM)
                
                try:
                    process.wait(timeout=5)
                    log_file.write(f"Process exited with return code {process.returncode} after SIGTERM\n")
                    assert process.returncode in [0, -15], f"Process returned unexpected code {process.returncode} after SIGTERM"
                
                except subprocess.TimeoutExpired:
                    # Last resort: SIGKILL
                    log_file.write("Process didn't respond to SIGTERM, using SIGKILL\n")
                    process.kill()
                    process.wait()
                    log_file.write(f"Process killed with return code {process.returncode}\n")
                    pytest.fail("Process did not respond to termination signals")
        
        finally:
            # Ensure process is terminated
            if process.poll() is None:
                process.kill()
                process.wait()
                log_file.write("Process had to be forcibly terminated\n")
    
    logger.info(f"Pipeline termination test results written to {log_file_path}")


# ---------------------------------------------------------
# Resource Download Tests
# ---------------------------------------------------------

def test_resource_downloader():
    """Test the resource downloader module."""
    try:
        from hailo_apps_infra.installation.download_resources import load_config
        
        # Test that we can load the configuration
        config = load_config()
        assert "groups" in config, "Resource config missing 'groups' section"
        assert "models" in config, "Resource config missing 'models' section"
        
        logger.info(f"Resource configuration loaded successfully with {len(config.get('models', {}))} models")
        
        # Test the download mechanism with a fake resource (but don't actually download)
        # Only mock or trace the functionality
        hailo_arch = detect_hailo_arch() or "hailo8"  # Default to hailo8 if not detected
        
        # Find some available models for this architecture
        available_models = []
        for name, model in config.get("models", {}).items():
            if model.get("arch") == hailo_arch:
                available_models.append(name)
        
        if available_models:
            logger.info(f"Found {len(available_models)} models compatible with {hailo_arch}: {', '.join(available_models[:5])}...")
        else:
            logger.warning(f"No models found for {hailo_arch} architecture")
        
    except ImportError:
        pytest.skip("Could not import download_resources module")
    except Exception as e:
        logger.error(f"Error testing resource downloader: {e}")
        pytest.fail(f"Resource downloader test failed: {e}")


if __name__ == "__main__":
    pytest.main(["-v", __file__])