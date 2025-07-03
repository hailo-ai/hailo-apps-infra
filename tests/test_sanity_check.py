import pytest
import subprocess
import os
import sys
import importlib
from pathlib import Path
import logging
from hailo_apps.hailo_app_python.core.common.installation_utils import (
    detect_host_arch,
    detect_hailo_arch,
    detect_pkg_installed
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sanity-tests")


def test_check_hailo_runtime_installed():
    """Test if the Hailo runtime is installed."""
    try:
        subprocess.run(['hailortcli', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Hailo runtime is installed.")
    except subprocess.CalledProcessError:
        pytest.fail("Error: Hailo runtime is not installed or not in PATH.")
    except FileNotFoundError:
        pytest.skip("Hailo runtime is not installed - skipping test on non-Hailo system.")

# TODO - Uncomment this test when the required files are changed to the current structure
# def test_check_required_files():
#     """Test if required project files and directories exist."""
#     project_root = Path(__file__).resolve().parents[1]
    
#     # Core files at project root
#     core_files = [
#         'LICENSE',
#         'MANIFEST.in',
#         'meson.build',
#         'pyproject.toml',
#         'README.md',
#         'requirements.txt',
#         'run_tests.sh',
#         'install.sh'
#     ]
    
#     # Script files
#     script_files = [
#         'scripts/compile_postprocess.sh',
#         'scripts/download_resources.sh',
#         'scripts/hailo_installation_script.sh'
#     ]
    
#     # Documentation files
#     doc_files = [
#         'doc/developer_guide.md',
#         'doc/development_guide.md',
#         'doc/installation_guide.md',
#         'doc/usage_of_all_pipelines.md'
#     ]
    
#     # C++ files
#     cpp_files = [
#         'cpp/depth_estimation.cpp',
#         'cpp/depth_estimation.hpp',
#         'cpp/hailo_nms_decode.hpp',
#         'cpp/__init__.py',
#         'cpp/mask_decoding.hpp',
#         'cpp/meson.build',
#         'cpp/remove_labels.cpp',
#         'cpp/remove_labels.hpp',
#         'cpp/yolo_hailortpp.cpp',
#         'cpp/yolo_hailortpp.hpp',
#         'cpp/yolov5seg.cpp',
#         'cpp/yolov5seg.hpp',
#         'cpp/yolov8pose_postprocess.cpp',
#         'cpp/yolov8pose_postprocess.hpp'
#     ]
    
#     # hailo_apps_infra modules and their internal files
#     module_files = [
#         # Common module
#         'hailo_apps_infra/common/pyproject.toml',
#         'hailo_apps_infra/common/hailo_common/get_config_values.py',
#         'hailo_apps_infra/common/hailo_common/get_usb_camera.py',
#         'hailo_apps_infra/common/hailo_common/common.py',
#         'hailo_apps_infra/common/hailo_common/__init__.py',
#         'hailo_apps_infra/common/hailo_common/test_utils.py',
#         'hailo_apps_infra/common/hailo_common/utils.py',
        
#         # Config module
#         'hailo_apps_infra/config/pyproject.toml',
#         'hailo_apps_infra/config/hailo_config/config.yaml',
#         'hailo_apps_infra/config/hailo_config/resources_config.yaml',
        
#         # GStreamer module
#         'hailo_apps_infra/gstreamer/pyproject.toml',
#         'hailo_apps_infra/gstreamer/hailo_gstreamer/gstreamer_app.py',
#         'hailo_apps_infra/gstreamer/hailo_gstreamer/gstreamer_helper_pipelines.py',
#         'hailo_apps_infra/gstreamer/hailo_gstreamer/__init__.py',
        
#         # Installation module
#         'hailo_apps_infra/installation/pyproject.toml',
#         'hailo_apps_infra/installation/hailo_installation/compile_cpp.py',
#         'hailo_apps_infra/installation/hailo_installation/download_resources.py',
#         'hailo_apps_infra/installation/hailo_installation/__init__.py',
#         'hailo_apps_infra/installation/hailo_installation/post_install.py',
#         'hailo_apps_infra/installation/hailo_installation/python_installation.py',
#         'hailo_apps_infra/installation/hailo_installation/set_env.py',
#         'hailo_apps_infra/installation/hailo_installation/validate_config.py',
        
#         # Pipelines module
#         'hailo_apps_infra/pipelines/pyproject.toml',
#         'hailo_apps_infra/pipelines/hailo_pipelines/depth_pipeline.py',
#         'hailo_apps_infra/pipelines/hailo_pipelines/detection_pipeline.py',
#         'hailo_apps_infra/pipelines/hailo_pipelines/detection_pipeline_simple.py',
#         'hailo_apps_infra/pipelines/hailo_pipelines/__init__.py',
#         'hailo_apps_infra/pipelines/hailo_pipelines/instance_segmentation_pipeline.py',
#         'hailo_apps_infra/pipelines/hailo_pipelines/pose_estimation_pipeline.py'
#     ]
    
#     required_paths = core_files + script_files + doc_files + cpp_files + module_files
#     missing = [path for path in required_paths if not (project_root / path).exists()]
    
#     if missing:
#         pytest.fail(f"The following required files or directories are missing: {', '.join(missing)}")

def test_check_resource_directory():
    """Test if the resources directory exists and has expected subdirectories."""
    resource_dir = Path("resources") or Path("/usr/local/hailo/resources")
    
    # Check if the resources directory exists
    if not resource_dir.exists():
        pytest.fail("Resources directory does not exist.")
    
    # Check for required resource files
    required_resources = [
        'example.mp4',
        'example_640.mp4',
        'libdepth_postprocess.so',
        'libyolo_hailortpp_postprocess.so',
        'libyolov5seg_postprocess.so',
        'libyolov8pose_postprocess.so'
    ]
    
    missing_resources = []
    for resource in required_resources:
        if not (resource_dir / resource).exists():
            missing_resources.append(resource)
    
    if missing_resources:
        logger.warning(f"The following resource files are missing: {', '.join(missing_resources)}")
        logger.warning("This might be normal if resources haven't been downloaded yet, but will cause tests to fail.")
    
    # Check for HEF files
    hef_files = list(resource_dir.glob("*.hef"))
    if not hef_files:
        logger.warning("No HEF files found in resources directory. Tests will likely fail.")
    else:
        logger.info(f"Found {len(hef_files)} HEF files: {', '.join(f.name for f in hef_files)}")
        
    # Check for JSON configuration files for models
    json_files = list(resource_dir.glob("*.json"))
    if not json_files:
        logger.warning("No JSON configuration files found in resources directory.")
    else:
        logger.info(f"Found {len(json_files)} JSON files: {', '.join(f.name for f in json_files)}")


def test_python_environment():
    """Test the Python environment and required packages."""
    # Check Python version
    assert sys.version_info >= (3, 6), "Python 3.6 or higher is required."
    
    # Critical packages that must be present for the framework to function
    critical_packages = [
        'gi',         # GStreamer bindings
        'numpy',      # Data manipulation
        'opencv-python',  # Computer vision
        'hailo',      # Hailo API
    ]
    
    # Additional packages that are useful but not critical
    additional_packages = [
        'setproctitle',
        'python-dotenv',
    ]
    
    # Test critical packages first
    missing_critical = []
    for package in critical_packages:
        try:
            if package == 'opencv-python':
                import cv2
                print(f"opencv-python is installed. Version: {cv2.__version__}")
            else:
                mod = importlib.import_module(package)
                print(f"{package} is installed.")
        except ImportError:
            missing_critical.append(package)
    
    if missing_critical:
        pytest.fail(f"Critical packages missing: {', '.join(missing_critical)}")
    
    # Test additional packages
    missing_additional = []
    for package in additional_packages:
        try:
            importlib.import_module(package)
            print(f"{package} is installed.")
        except ImportError:
            missing_additional.append(package)
    
    if missing_additional:
        print(f"Warning: Some additional packages are missing: {', '.join(missing_additional)}")


def test_gstreamer_installation():
    """Test GStreamer installation and required plugins."""
    try:
        # Test basic GStreamer installation
        result = subprocess.run(['gst-inspect-1.0', '--version'], 
                                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"GStreamer is installed: {result.stdout.decode('utf-8').strip()}")
        
        # Test critical GStreamer elements
        critical_elements = [
            'videotestsrc',    # Basic video source 
            'appsink',         # Used for custom callbacks
            'videoconvert',    # Used for format conversion
            'autovideosink',   # Display sink
        ]
        
        missing_elements = []
        for element in critical_elements:
            result = subprocess.run(['gst-inspect-1.0', element], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                missing_elements.append(element)
        
        if missing_elements:
            pytest.fail(f"Critical GStreamer elements missing: {', '.join(missing_elements)}")
        
    except subprocess.CalledProcessError:
        pytest.fail("GStreamer is not properly installed or not in PATH.")
    except FileNotFoundError:
        pytest.fail("GStreamer command-line tools are not installed.")


def test_hailo_gstreamer_elements():
    """Test if Hailo GStreamer elements are installed."""
    # First check if we have a Hailo device
    hailo_arch = detect_hailo_arch()
    if hailo_arch is None:
        pytest.skip("No Hailo device detected - skipping Hailo GStreamer element check.")
        
    try:
        # Check for Hailo elements
        hailo_elements = [
            'hailonet',        # Inference element
            'hailofilter',     # Used for post-processing
        ]
        
        missing_elements = []
        for element in hailo_elements:
            result = subprocess.run(['gst-inspect-1.0', element], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                missing_elements.append(element)
        
        if missing_elements:
            pytest.fail(f"Hailo GStreamer elements missing: {', '.join(missing_elements)}. "
                        f"These are required for Hailo inference pipelines.")
        else:
            logger.info("All Hailo GStreamer elements are installed.")
            
    except subprocess.CalledProcessError:
        pytest.fail("GStreamer installation issue - cannot check Hailo elements.")
    except FileNotFoundError:
        pytest.fail("GStreamer command-line tools not found - cannot check Hailo elements.")


def test_arch_specific_environment():
    """Test architecture-specific environment components."""
    # Use the utility function from hailo_rpi_common
    device_arch = detect_host_arch()
    logger.info(f"Detected device architecture: {device_arch}")
    
    # Arch-specific checks
    if device_arch == "rpi":
        # Raspberry Pi specific checks
        try:
            import picamera2
            logger.info("picamera2 is installed for Raspberry Pi.")
        except ImportError:
            logger.warning("picamera2 is not installed. This is needed for using the RPi camera module.")
    
    elif device_arch == "arm":
        # General ARM checks (non-RPi)
        logger.info("Running on ARM architecture (non-Raspberry Pi).")
    
    elif device_arch == "x86":
        # x86 specific checks
        logger.info("Running on x86 architecture.")
    
    else:
        logger.warning(f"Unknown architecture: {device_arch}")


def test_setup_installation():
    """Test package installation from setup.py."""
    try:
        result = subprocess.run(['pip', 'list'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True)
        
        if "hailo-apps-infra" in result.stdout:
            logger.info("hailo-apps-infra package is installed.")
        else:
            logger.warning("hailo-apps-infra package is not installed. Run 'pip install -e .' to install in development mode.")
            
    except subprocess.CalledProcessError:
        pytest.fail("Failed to check pip packages.")


def test_environment_variables():
    """Test if required environment variables are set."""
    # Check for key environment variables
    env_vars = {
        "DEVICE_ARCH": detect_host_arch(),
        "HAILO_ARCH": detect_hailo_arch() or "unknown",
    }
    
    # Check if environment variables are set
    for var, expected_value in env_vars.items():
        actual_value = os.environ.get(var)
        if actual_value:
            logger.info(f"Environment variable {var}={actual_value}")
            # Optional: verify if variable matches expected value
            if actual_value != expected_value and expected_value != "unknown":
                logger.warning(f"Environment variable {var} has value {actual_value}, but detected value is {expected_value}")
        else:
            logger.warning(f"Environment variable {var} is not set")
    
    # Check for TAPPAS-related environment variables
    if "TAPPAS_POST_PROC_DIR" in os.environ:
        post_proc_dir = os.environ["TAPPAS_POST_PROC_DIR"]
        logger.info(f"TAPPAS_POST_PROC_DIR={post_proc_dir}")
        
        # Check if directory exists
        if post_proc_dir and not os.path.exists(post_proc_dir):
            logger.warning(f"TAPPAS_POST_PROC_DIR points to non-existent directory: {post_proc_dir}")
    else:
        # Check which TAPPAS variant is installed
        if detect_pkg_installed("hailo-tappas"):
            logger.warning("hailo-tappas is installed but TAPPAS_POST_PROC_DIR is not set")
        elif detect_pkg_installed("hailo-tappas-core"):
            logger.warning("hailo-tappas-core is installed but TAPPAS_POST_PROC_DIR is not set")
            
    # Check if .env file exists
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.exists():
        logger.info(f".env file exists at {env_file}")
        # Optionally read and check the content
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
                logger.info(f".env file content: {env_content.strip()}")
        except Exception as e:
            logger.warning(f"Could not read .env file: {e}")
    else:
        logger.warning(f".env file does not exist at {env_file}")
        logger.warning("You may need to run the setup script to create it.")


if __name__ == "__main__":
    pytest.main(["-v", __file__])