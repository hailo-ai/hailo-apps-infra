"""Core helpers: arch detection, parser, buffer utils."""

import argparse
import os
import queue
from pathlib import Path

from dotenv import load_dotenv

from .defines import (
    DEFAULT_DOTENV_PATH,
    DEFAULT_LOCAL_RESOURCES_PATH,
    DEPTH_MODEL_NAME,
    DEPTH_PIPELINE,
    DETECTION_MODEL_NAME_H8,
    DETECTION_MODEL_NAME_H8L,
    DETECTION_PIPELINE,
    DIC_CONFIG_VARIANTS,
    FACE_DETECTION_MODEL_NAME_H8,
    FACE_DETECTION_MODEL_NAME_H8L,
    FACE_DETECTION_PIPELINE,
    FACE_RECOGNITION_MODEL_NAME_H8,
    FACE_RECOGNITION_MODEL_NAME_H8L,
    FACE_RECOGNITION_PIPELINE,
    FACE_RECON_DIR_NAME,
    HAILO8_ARCH,
    MULTI_SOURCE_DIR_NAME,
    HAILO10H_ARCH,
    HAILO_ARCH_KEY,
    HAILO_FILE_EXTENSION,
    INSTANCE_SEGMENTATION_MODEL_NAME_H8,
    INSTANCE_SEGMENTATION_MODEL_NAME_H8L,
    INSTANCE_SEGMENTATION_PIPELINE,
    POSE_ESTIMATION_MODEL_NAME_H8,
    POSE_ESTIMATION_MODEL_NAME_H8L,
    POSE_ESTIMATION_PIPELINE,
    RESOURCES_JSON_DIR_NAME,
    RESOURCES_MODELS_DIR_NAME,
    # for get_resource_path
    RESOURCES_PHOTOS_DIR_NAME,
    RESOURCES_ROOT_PATH_DEFAULT,
    RESOURCES_SO_DIR_NAME,
    RESOURCES_VIDEOS_DIR_NAME,
    SIMPLE_DETECTION_MODEL_NAME,
    SIMPLE_DETECTION_PIPELINE,
)
from .hailo_logger import get_logger
from .installation_utils import detect_hailo_arch

hailo_logger = get_logger(__name__)


def load_environment(env_file=DEFAULT_DOTENV_PATH, required_vars=None) -> bool:
    hailo_logger.debug(f"Loading environment from: {env_file}")
    if env_file is None:
        env_file = DEFAULT_DOTENV_PATH
    load_dotenv(dotenv_path=env_file)

    env_path = Path(env_file)
    if not os.path.exists(env_path):
        hailo_logger.warning(f".env file not found: {env_file}")
        print(f"⚠️ .env file not found: {env_file}")
        return
    if not os.access(env_path, os.R_OK):
        hailo_logger.warning(f".env file not readable: {env_file}")
        print(f"⚠️ .env file not readable: {env_file}")
        return
    if not os.access(env_path, os.W_OK):
        hailo_logger.warning(f".env file not writable: {env_file}")
        print(f"⚠️ .env file not writable: {env_file}")
        return
    if not os.access(env_path, os.F_OK):
        hailo_logger.warning(f".env file not found (F_OK): {env_file}")
        print(f"⚠️ .env file not found: {env_file}")
        return

    if required_vars is None:
        required_vars = DIC_CONFIG_VARIANTS
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)

    if missing:
        hailo_logger.warning(f"Missing environment variables: {missing}")
        print("⚠️ Missing environment variables: %s", ", ".join(missing))
        return False
    hailo_logger.info("All required environment variables loaded successfully.")
    print("✅ All required environment variables loaded.")
    return True


def get_default_parser():
    hailo_logger.debug("Creating default argparse parser.")
    parser = argparse.ArgumentParser(description="Hailo App Help")
    parser.add_argument(
        "--input", "-i", type=str, default=None,
        help="Input source. Can be a file, USB (webcam), RPi camera (CSI camera module) or ximage. \
        For RPi camera use '-i rpi' \
        For automatically detect a connected usb camera, use '-i usb' \
        For manually specifying a connected usb camera, use '-i /dev/video<X>' \
        Defaults to application specific video."
    )
    parser.add_argument("--use-frame", "-u", action="store_true", help="Use frame from the callback function")
    parser.add_argument("--show-fps", "-f", action="store_true", help="Print FPS on sink")
    parser.add_argument(
            "--arch",
            default=None,
            choices=['hailo8', 'hailo8l', 'hailo10h'],
            help="Specify the Hailo architecture (hailo8 or hailo8l or hailo10h). Default is None , app will run check.",
    )
    parser.add_argument(
            "--hef-path",
            default=None,
            help="Path to HEF file",
    )
    parser.add_argument(
        "--disable-sync", action="store_true",
        help="Disables display sink sync, will run as fast as possible. Relevant when using file source."
    )
    parser.add_argument(
        "--disable-callback", action="store_true",
        help="Disables the user's custom callback function in the pipeline. Use this option to run the pipeline without invoking the callback logic."
    )
    parser.add_argument("--dump-dot", action="store_true", help="Dump the pipeline graph to a dot file pipeline.dot")
    parser.add_argument(
        "--frame-rate", "-r", type=int, default=30,
        help="Frame rate of the video source. Default is 30."
    )
    return parser


def get_model_name(pipeline_name: str, arch: str) -> str:
    hailo_logger.debug(f"Getting model name for pipeline={pipeline_name}, arch={arch}")
    is_h8 = arch in (HAILO8_ARCH, HAILO10H_ARCH)
    pipeline_map = {
        DEPTH_PIPELINE: DEPTH_MODEL_NAME,
        SIMPLE_DETECTION_PIPELINE: SIMPLE_DETECTION_MODEL_NAME,
        DETECTION_PIPELINE: DETECTION_MODEL_NAME_H8 if is_h8 else DETECTION_MODEL_NAME_H8L,
        INSTANCE_SEGMENTATION_PIPELINE: INSTANCE_SEGMENTATION_MODEL_NAME_H8
        if is_h8
        else INSTANCE_SEGMENTATION_MODEL_NAME_H8L,
        POSE_ESTIMATION_PIPELINE: POSE_ESTIMATION_MODEL_NAME_H8
        if is_h8
        else POSE_ESTIMATION_MODEL_NAME_H8L,
        FACE_DETECTION_PIPELINE: FACE_DETECTION_MODEL_NAME_H8
        if is_h8
        else FACE_DETECTION_MODEL_NAME_H8L,
        FACE_RECOGNITION_PIPELINE: FACE_RECOGNITION_MODEL_NAME_H8
        if is_h8
        else FACE_RECOGNITION_MODEL_NAME_H8L,
    }
    name = pipeline_map[pipeline_name]
    hailo_logger.debug(f"Resolved model name: {name}")
    return name


def get_resource_path(
    pipeline_name: str, resource_type: str,arch: str, model: str | None = None
) -> Path | None:
    hailo_logger.debug(
        f"Getting resource path for pipeline={pipeline_name}, resource_type={resource_type}, model={model}"
    )
    root = Path(RESOURCES_ROOT_PATH_DEFAULT)
    # arch = os.getenv(HAILO_ARCH_KEY, detect_hailo_arch())
    if not arch:
        hailo_logger.error("Could not detect Hailo architecture.")
        return None

    if resource_type == RESOURCES_SO_DIR_NAME and model:
        return root / RESOURCES_SO_DIR_NAME / model
    if resource_type == RESOURCES_VIDEOS_DIR_NAME and model:
        return root / RESOURCES_VIDEOS_DIR_NAME / model
    if resource_type == RESOURCES_PHOTOS_DIR_NAME and model:
        return root / RESOURCES_PHOTOS_DIR_NAME / model
    if resource_type == RESOURCES_JSON_DIR_NAME and model:
        return root / RESOURCES_JSON_DIR_NAME / model
    if resource_type == FACE_RECON_DIR_NAME and model:
        return root / FACE_RECON_DIR_NAME / model
    if resource_type == MULTI_SOURCE_DIR_NAME and model:
        return (root / MULTI_SOURCE_DIR_NAME / model)
    if resource_type == DEFAULT_LOCAL_RESOURCES_PATH and model:
        return root / DEFAULT_LOCAL_RESOURCES_PATH / model

    if resource_type == RESOURCES_MODELS_DIR_NAME:
        if model:
            model_path = root / RESOURCES_MODELS_DIR_NAME / arch / model
            if "." in model:
                return model_path.with_name(model_path.name + HAILO_FILE_EXTENSION)
            return model_path.with_suffix(HAILO_FILE_EXTENSION)
        if pipeline_name:
            name = get_model_name(pipeline_name, arch)
            name_path = root / RESOURCES_MODELS_DIR_NAME / arch / name
            if "." in name:
                return name_path.with_name(name_path.name + HAILO_FILE_EXTENSION)
            return name_path.with_suffix(HAILO_FILE_EXTENSION)
    return None


class FIFODropQueue(queue.Queue):
    def put(self, item, block=False, timeout=None):
        if self.full():
            hailo_logger.debug("Queue full, dropping oldest item.")
            self.get_nowait()
        super().put(item, block, timeout)
