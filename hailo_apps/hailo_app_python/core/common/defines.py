from pathlib import Path

# Base Defaults
HAILO8_ARCH = "hailo8"
HAILO8L_ARCH = "hailo8l"
HAILO10H_ARCH = "hailo10h"
AUTO_DETECT = "auto"
HAILO_TAPPAS = "hailo-tappas"
HAILO_TAPPAS_CORE = "hailo-tappas-core"
HAILO_TAPPAS_CORE_PYTHON = "hailo-tappas-core-python-binding"
HAILO_TAPPAS_CORE_PYTHON_NAMES = [HAILO_TAPPAS_CORE_PYTHON, "tappas-core-python-binding" , HAILO_TAPPAS_CORE]
HAILORT_PACKAGE = "hailort"
HAILO_FILE_EXTENSION = ".hef"
MODEL_ZOO_URL = "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled"
RESOURCES_ROOT_PATH_DEFAULT = "/usr/local/hailo/resources" # Do Not Change!

# Core defaults
ARM_POSSIBLE_NAME = ["arm", "aarch64"]
X86_POSSIBLE_NAME = ["x86", "amd64", "x86_64"]
RPI_POSSIBLE_NAME = ["rpi", "raspberrypi", "pi"]
HAILO8_ARCH_CAPS = "HAILO8"
HAILO8L_ARCH_CAPS = "HAILO8L"
HAILO10H_ARCH_CAPS = "HAILO15H"
HAILO_FW_CONTROL_CMD = "hailortcli fw-control identify"
X86_NAME_I = "x86"
RPI_NAME_I = "rpi"
ARM_NAME_I = "arm"
LINUX_SYSTEM_NAME_I = "linux"
UNKNOWN_NAME_I = "unknown"
USB_CAMERA = "usb"
X86_LINUX_PLATFORM_TAG = "linux_x86_64"
ARM_LINUX_PLATFORM_TAG = "linux_aarch64"
CONFIG_DEFAULT_NAME = "config.yaml"
JSON_FILE_EXTENSION = ".json"

# CLI defaults
PYTHON_CMD = "python3"
PIP_CMD = "pip3"
VENV_CREATE_CMD = "python3 -m venv"

# Base project paths
REPO_ROOT = Path(__file__).resolve().parents[4]

# Default config paths (now in top-level “config” folder)
DEFAULT_CONFIG_PATH            = str(REPO_ROOT / "config" / "config.yaml")
DEFAULT_RESOURCES_CONFIG_PATH  = str(REPO_ROOT / "config" / "resources_config.yaml")

# Symlink, dotenv, local resources defaults
DEFAULT_RESOURCES_SYMLINK_PATH = str(REPO_ROOT / "resources")        # e.g. created by post-install
DEFAULT_DOTENV_PATH            = str(REPO_ROOT / ".env")             # your env file lives here
DEFAULT_LOCAL_RESOURCES_PATH   = str(REPO_ROOT / "local_resources")  # bundled GIFs, JSON, etc.

# Supported config options
VALID_HAILORT_VERSION = [AUTO_DETECT, "4.20.0", "4.21.0", "4.22.0"]
VALID_TAPPAS_VERSION = [AUTO_DETECT, "3.30.0", "3.31.0", "3.32.0"]
VALID_MODEL_ZOO_VERSION = ["v2.13.0", "v2.14.0", "v2.15.0"]
VALID_HOST_ARCH = [AUTO_DETECT, "x86", "rpi", "arm"]
VALID_HAILO_ARCH = [AUTO_DETECT, HAILO8_ARCH, HAILO8L_ARCH, HAILO10H_ARCH]
VALID_SERVER_URL = ["http://dev-public.hailo.ai/2025_01"]
VALID_TAPPAS_VARIANT = [AUTO_DETECT, HAILO_TAPPAS, HAILO_TAPPAS_CORE]

# Config key constants
HAILORT_VERSION_KEY = "hailort_version"
TAPPAS_VERSION_KEY = "tappas_version"
MODEL_ZOO_VERSION_KEY = "model_zoo_version"
HOST_ARCH_KEY = "host_arch"
HAILO_ARCH_KEY = "hailo_arch"
SERVER_URL_KEY = "server_url"
TAPPAS_VARIANT_KEY = "tappas_variant"
RESOURCES_PATH_KEY = "resources_path"
VIRTUAL_ENV_NAME_KEY = "virtual_env_name"
TAPPAS_POSTPROC_PATH_KEY = "tappas_postproc_path"
HAILO_APPS_INFRA_PATH_KEY = "hailo_apps_infra_path"

# Environment variable groups
DIC_CONFIG_VARIANTS = [
    HAILORT_VERSION_KEY,
    TAPPAS_VERSION_KEY,
    MODEL_ZOO_VERSION_KEY,
    HOST_ARCH_KEY,
    HAILO_ARCH_KEY,
    SERVER_URL_KEY,
    TAPPAS_VARIANT_KEY,
    RESOURCES_PATH_KEY,
    VIRTUAL_ENV_NAME_KEY,
    TAPPAS_POSTPROC_PATH_KEY,
]

# Default config values
HAILORT_VERSION_DEFAULT = AUTO_DETECT
TAPPAS_VERSION_DEFAULT = AUTO_DETECT
TAPPAS_VARIANT_DEFAULT = AUTO_DETECT
HOST_ARCH_DEFAULT = AUTO_DETECT
HAILO_ARCH_DEFAULT = AUTO_DETECT
MODEL_ZOO_VERSION_DEFAULT = "v2.14.0"
SERVER_URL_DEFAULT = "http://dev-public.hailo.ai/2025_01"
RESOURCES_PATH_DEFAULT = RESOURCES_ROOT_PATH_DEFAULT
VIRTUAL_ENV_NAME_DEFAULT = "hailo_infra_venv"
STORAGE_PATH_DEFAULT = str(Path(RESOURCES_ROOT_PATH_DEFAULT) / "storage_deb_whl_dir")
# Default Tappas post-processing directory
import subprocess

TAPPAS_POSTPROC_PATH_DEFAULT = subprocess.check_output(
    ["pkg-config", "--variable=tappas_postproc_lib_dir", "hailo-tappas-core"],
    text=True
).strip()

# Resource groups for download_resources
RESOURCES_GROUP_DEFAULT = "default"
RESOURCES_GROUP_ALL = "all"
RESOURCES_GROUP_HAILO8 = "hailo8"
RESOURCES_GROUP_HAILO8L = "hailo8l"
RESOURCES_GROUP_RETRAIN = "retrain"

RESOURCES_GROUPS_MAP = [ RESOURCES_GROUP_DEFAULT,
                        RESOURCES_GROUP_ALL,
                        RESOURCES_GROUP_HAILO8,
                        RESOURCES_GROUP_HAILO8L,
                        RESOURCES_GROUP_RETRAIN]

# YAML config file keys
RESOURCES_CONFIG_DEFAULTS_KEY = "defaults"
RESOURCES_CONFIG_GROUPS_KEY = "models"
RESOURCES_CONFIG_VIDEOS_KEY = "videos"

# Resources directory structure
RESOURCES_MODELS_DIR_NAME = "models"
RESOURCES_VIDEOS_DIR_NAME = "videos"
RESOURCES_SO_DIR_NAME = "so"
RESOURCES_PHOTOS_DIR_NAME = "photos"
RESOURCES_GIF_DIR_NAME = "gifs"
RESOURCES_JSON_DIR_NAME = "json"
RESOURCE_STORAGE_DIR_NAME = "installation-storage"
RESOURCE_FACE_RECON_TRAIN = "face_recon/train"
RESOURCE_FACE_RECON_SAMPLES = "face_recon/samples"
RESOURCES_DIRS_MAP = [
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCES_MODELS_DIR_NAME}/{HAILO8_ARCH}",
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCES_MODELS_DIR_NAME}/{HAILO8L_ARCH}",
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCES_SO_DIR_NAME}",
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCES_PHOTOS_DIR_NAME}",
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCES_GIF_DIR_NAME}",
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCES_JSON_DIR_NAME}",
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCES_VIDEOS_DIR_NAME}",
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCE_STORAGE_DIR_NAME}",
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCE_FACE_RECON_TRAIN}",
    f"{RESOURCES_ROOT_PATH_DEFAULT}/{RESOURCE_FACE_RECON_SAMPLES}",
]

# GStreamer defaults
GST_REQUIRED_VERSION = "1.0"

# Depth pipeline defaults
DEPTH_APP_TITLE = "Hailo Depth App"
DEPTH_PIPELINE = "depth"
DEPTH_POSTPROCESS_SO_FILENAME = "libdepth_postprocess.so"
DEPTH_POSTPROCESS_FUNCTION = "filter_scdepth"
DEPTH_MODEL_NAME = "scdepthv3"

# Simple detection pipeline defaults
SIMPLE_DETECTION_APP_TITLE = "Hailo Simple Detection App"
SIMPLE_DETECTION_PIPELINE = "simple_detection"
SIMPLE_DETECTION_VIDEO_NAME = "example_640.mp4"
SIMPLE_DETECTION_MODEL_NAME = "yolov6n"
SIMPLE_DETECTION_POSTPROCESS_SO_FILENAME = "libyolo_hailortpp_postprocess.so"
SIMPLE_DETECTION_POSTPROCESS_FUNCTION = "filter"

# Detection pipeline defaults
DETECTION_APP_TITLE = "Hailo Detection App"
DETECTION_PIPELINE = "detection"
DETECTION_MODEL_NAME_H8 = "yolov8m"
DETECTION_MODEL_NAME_H8L = "yolov8s"
DETECTION_POSTPROCESS_SO_FILENAME = "libyolo_hailortpp_postprocess.so"
DETECTION_POSTPROCESS_FUNCTION = "filter_letterbox"
RETRAINING_BARCODE_LABELS_JSON_NAME = "barcode_labels.json"
RETRAINING_MODEL_NAME = "yolov8s-hailo8l-barcode"

# Instance segmentation pipeline defaults
INSTANCE_SEGMENTATION_APP_TITLE = "Hailo Instance Segmentation App"
INSTANCE_SEGMENTATION_PIPELINE = "instance_segmentation"
INSTANCE_SEGMENTATION_POSTPROCESS_SO_FILENAME = "libyolov5seg_postprocess.so"
INSTANCE_SEGMENTATION_POSTPROCESS_FUNCTION = "filter_letterbox"
INSTANCE_SEGMENTATION_MODEL_NAME_H8 = "yolov5m_seg"
INSTANCE_SEGMENTATION_MODEL_NAME_H8L = "yolov5n_seg"

# Pose estimation pipeline defaults
POSE_ESTIMATION_APP_TITLE = "Hailo Pose Estimation App"
POSE_ESTIMATION_PIPELINE = "pose_estimation"
POSE_ESTIMATION_POSTPROCESS_SO_FILENAME = "libyolov8pose_postprocess.so"
POSE_ESTIMATION_POSTPROCESS_FUNCTION = "filter_letterbox"
POSE_ESTIMATION_MODEL_NAME_H8 = "yolov8m_pose"
POSE_ESTIMATION_MODEL_NAME_H8L = "yolov8s_pose"

# Face recognition pipeline defaults
FACE_DETECTION_PIPELINE = 'face_detection'
FACE_DETECTION_MODEL_NAME_H8 = 'scrfd_10g'
FACE_DETECTION_MODEL_NAME_H8L = 'scrfd_2.5g'
FACE_RECOGNITION_PIPELINE = 'face_recognition'
FACE_RECOGNITION_MODEL_NAME_H8 = 'arcface_mobilefacenet'
FACE_RECOGNITION_MODEL_NAME_H8L = 'arcface_mobilefacenet_h8l'
FACE_DETECTION_POSTPROCESS_SO_FILENAME = "libscrfd.so"
FACE_RECOGNITION_POSTPROCESS_SO_FILENAME = "libface_recognition_post.so"
FACE_ALIGN_POSTPROCESS_SO_FILENAME = "libvms_face_align.so"
FACE_CROP_POSTPROCESS_SO_FILENAME = "libvms_croppers.so"
TRACKER_UPDATE_POSTPROCESS_SO_FILENAME = "libtracker_update.so"
FACE_RECOGNITION_VIDEO_NAME = "face_recognition.mp4"
FACE_RECON_DIR_NAME = "face_recon"
FACE_RECON_DATABASE_DIR_NAME = "database"
FACE_RECON_TRAIN_DIR_NAME = "train"
FACE_RECON_SAMPLES_DIR_NAME = "samples"
FACE_RECON_LOCAL_SAMPLES_DIR_NAME = "faces"
FACE_DETECTION_JSON_NAME = "scrfd.json"
FACE_ALGO_PARAMS_JSON_NAME = "face_recon_algo_params.json"

# Multisource pipeline defaults
MULTISOURCE_APP_TITLE = "Hailo Multisource App"
MULTISOURCE_PIPELINE = "multisource"
MULTISOURCE_POSTPROCESS_SO_FILENAME = "libdepth_postprocess.so"
MULTISOURCE_POSTPROCESS_FUNCTION = "filter_scdepth"
MULTISOURCE_MODEL_NAME = "scdepthv3"

# Installation & subprocess defaults
PIP_SHOW_TIMEOUT = 5  # seconds
INSTALL_LOG = "env_setup.log"

# Testing defaults
TEST_RUN_TIME = 10  # seconds
TERM_TIMEOUT = 5    # seconds

# USB device discovery
UDEV_CMD = "udevadm"

# Miscellaneous
EPSILON = 1e-6

# Compile_cpp defaults
MODE_RELEASE = "release"
MODE_DEBUG = "debug"
MODE_CLEAN = "clean"

# Download resources defaults
DEFAULT_VIDEO_FORMAT_SUFFIX = ".mp4"

HAILO_RGB_VIDEO_FORMAT = "RGB"
HAILO_BGR_VIDEO_FORMAT = "BGR"
HAILO_YUYV_VIDEO_FORMAT = "YUYV"
HAILO_NV12_VIDEO_FORMAT = "NV12"

# Video examples
BASIC_PIPELINES_VIDEO_EXAMPLE_NAME = "example.mp4"
BASIC_PIPELINES_VIDEO_EXAMPLE_640_NAME = "example_640.mp4"
BARCODE_VIDEO_EXAMPLE_NAME = 'barcode.mp4'

# Photos resources
HAILO_LOGO_PHOTO_NAME = "logo.png"

# Gstreamer pipeline defaults
GST_VIDEO_SINK = "autovideosink"
