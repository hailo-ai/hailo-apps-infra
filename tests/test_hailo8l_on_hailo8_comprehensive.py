"""
Comprehensive test suite for running Hailo8L models on Hailo 8 architecture.

This test suite provides a unified way to test all Hailo8L models on Hailo 8
for different pipeline types, including detection, pose estimation, segmentation,
face recognition, multisource, REID, and tiling pipelines.
"""

import logging
import os
from pathlib import Path

import pytest

from hailo_apps.hailo_app_python.core.common.installation_utils import detect_hailo_arch
from hailo_apps.hailo_app_python.core.common.defines import (
    HAILO8_ARCH,
    HAILO8L_ARCH,
    RESOURCES_ROOT_PATH_DEFAULT,
)
from hailo_apps.hailo_app_python.core.common.test_utils import run_pipeline_cli_with_args

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_hailo8l_on_hailo8_comprehensive")


class Hailo8LOnHailo8Tester:
    """Helper class to run Hailo8L models on Hailo 8 architecture."""

    def __init__(self):
        self.hailo_arch = detect_hailo_arch()
        self.log_dir = "logs/h8l_on_h8_comprehensive"
        os.makedirs(self.log_dir, exist_ok=True)

        # Define Hailo8L models for each pipeline type
        self.h8l_models = {
            "detection": ["yolov5m_wo_spp", "yolov6n", "yolov8s", "yolov8m", "yolov11n", "yolov11s"],
            "pose_estimation": ["yolov8s_pose"],
            "segmentation": ["yolov5m_seg", "yolov5n_seg"],
            "face_recognition": ["scrfd_2.5g", "arcface_mobilefacenet_h8l"],
            "multisource": ["yolov5m_wo_spp", "yolov6n", "yolov8s", "yolov8m", "yolov11n", "yolov11s"],
            "reid": ["yolov5m_wo_spp", "yolov6n", "yolov8s", "yolov8m", "yolov11n", "yolov11s"],
            "tiling": ["yolov6n", "ssd_mobilenet_v1_visdrone"]
        }

        # CLI commands for each pipeline type
        self.cli_commands = {
            "detection": "hailo-detect",
            "pose_estimation": "hailo-pose",
            "segmentation": "hailo-seg",
            "face_recognition": "hailo-face-recon",
            "multisource": "hailo-multisource",
            "reid": "hailo-reid",
            "tiling": "hailo-tiling"
        }

    def run_model(self, pipeline_type, model_name, extra_args=None):
        """Run a specific Hailo8L model on Hailo 8 for a given pipeline type.

        Args:
            pipeline_type: Type of pipeline (detection, pose_estimation, etc.)
            model_name: Name of the Hailo8L model to run
            extra_args: Additional arguments to pass to the pipeline

        Returns:
            tuple: (stdout, stderr, success)
        """
        if self.hailo_arch != HAILO8_ARCH:
            logger.warning(f"Not running on Hailo 8 architecture (current: {self.hailo_arch})")
            return b"", b"", False

        # Build full HEF path for Hailo8L model
        hef_full_path = os.path.join(RESOURCES_ROOT_PATH_DEFAULT, "models", HAILO8L_ARCH, f"{model_name}.hef")

        # Get CLI command
        cli_command = self.cli_commands.get(pipeline_type)
        if not cli_command:
            logger.error(f"Unknown pipeline type: {pipeline_type}")
            return b"", b"", False

        # Prepare CLI arguments
        args = ["--hef-path", hef_full_path]

        # Add tiling-specific arguments for better testing
        if pipeline_type == "tiling":
            # Test different tiling configurations based on model type
            if "mobilenet" in model_name.lower():
                # For MobileNetSSD models, test single-scale mode
                args.extend(["--tiles-x", "2", "--tiles-y", "2"])
            else:
                # For YOLO models, test multi-scale mode
                args.extend(["--general-detection", "--multi-scale", "--scale-levels", "2"])

        if extra_args:
            args.extend(extra_args)

        # Create log file path
        log_file_path = os.path.join(self.log_dir, f"{pipeline_type}_{model_name}.log")

        try:
            logger.info(f"Testing {pipeline_type} with Hailo8L model: {model_name} on Hailo 8")
            stdout, stderr = run_pipeline_cli_with_args(cli_command, args, log_file_path)

            # Check for errors
            err_str = stderr.decode().lower() if stderr else ""
            success = "error" not in err_str and "traceback" not in err_str
            return stdout, stderr, success

        except Exception as e:
            logger.error(f"Exception while testing {model_name} on Hailo 8: {e}")
            return b"", str(e).encode(), False

    def run_pipeline_tests(self, pipeline_type):
        """Run all Hailo8L models for a specific pipeline type.

        Args:
            pipeline_type: Type of pipeline to test

        Returns:
            dict: Results for each model
        """
        if pipeline_type not in self.h8l_models:
            logger.error(f"Unknown pipeline type: {pipeline_type}")
            return {}

        models = self.h8l_models[pipeline_type]
        results = {}

        logger.info(f"Testing {pipeline_type} pipeline with {len(models)} Hailo8L models")

        for model in models:
            stdout, stderr, success = self.run_model(pipeline_type, model)

            results[model] = {
                "success": success,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
            }

            if success:
                logger.info(f"✓ {pipeline_type}: {model}")
            else:
                logger.error(f"✗ {pipeline_type}: {model}")

        return results


@pytest.fixture
def h8l_tester():
    """Fixture providing Hailo8LOnHailo8Tester instance."""
    return Hailo8LOnHailo8Tester()


def test_hailo8l_on_hailo8_detection(h8l_tester):
    """Test Hailo8L detection models on Hailo 8."""
    if h8l_tester.hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {h8l_tester.hailo_arch}")

    results = h8l_tester.run_pipeline_tests("detection")

    failed_models = [model for model, result in results.items() if not result["success"]]
    if failed_models:
        failure_details = "\n".join(
            [f"Model: {model}\nError: {results[model]['stderr']}\n" for model in failed_models]
        )
        pytest.fail(f"Failed Hailo8L detection models on Hailo 8:\n{failure_details}")


def test_hailo8l_on_hailo8_pose_estimation(h8l_tester):
    """Test Hailo8L pose estimation models on Hailo 8."""
    if h8l_tester.hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {h8l_tester.hailo_arch}")

    results = h8l_tester.run_pipeline_tests("pose_estimation")

    failed_models = [model for model, result in results.items() if not result["success"]]
    if failed_models:
        failure_details = "\n".join(
            [f"Model: {model}\nError: {results[model]['stderr']}\n" for model in failed_models]
        )
        pytest.fail(f"Failed Hailo8L pose estimation models on Hailo 8:\n{failure_details}")


def test_hailo8l_on_hailo8_segmentation(h8l_tester):
    """Test Hailo8L segmentation models on Hailo 8."""
    if h8l_tester.hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {h8l_tester.hailo_arch}")

    results = h8l_tester.run_pipeline_tests("segmentation")

    failed_models = [model for model, result in results.items() if not result["success"]]
    if failed_models:
        failure_details = "\n".join(
            [f"Model: {model}\nError: {results[model]['stderr']}\n" for model in failed_models]
        )
        pytest.fail(f"Failed Hailo8L segmentation models on Hailo 8:\n{failure_details}")


def test_hailo8l_on_hailo8_face_recognition(h8l_tester):
    """Test Hailo8L face recognition models on Hailo 8."""
    if h8l_tester.hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {h8l_tester.hailo_arch}")

    results = h8l_tester.run_pipeline_tests("face_recognition")

    failed_models = [model for model, result in results.items() if not result["success"]]
    if failed_models:
        failure_details = "\n".join(
            [f"Model: {model}\nError: {results[model]['stderr']}\n" for model in failed_models]
        )
        pytest.fail(f"Failed Hailo8L face recognition models on Hailo 8:\n{failure_details}")


def test_hailo8l_on_hailo8_multisource(h8l_tester):
    """Test Hailo8L models on Hailo 8 for multisource pipeline."""
    if h8l_tester.hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {h8l_tester.hailo_arch}")

    results = h8l_tester.run_pipeline_tests("multisource")

    failed_models = [model for model, result in results.items() if not result["success"]]
    if failed_models:
        failure_details = "\n".join(
            [f"Model: {model}\nError: {results[model]['stderr']}\n" for model in failed_models]
        )
        pytest.fail(f"Failed Hailo8L multisource models on Hailo 8:\n{failure_details}")


def test_hailo8l_on_hailo8_reid(h8l_tester):
    """Test Hailo8L models on Hailo 8 for REID pipeline."""
    if h8l_tester.hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {h8l_tester.hailo_arch}")

    results = h8l_tester.run_pipeline_tests("reid")

    failed_models = [model for model, result in results.items() if not result["success"]]
    if failed_models:
        failure_details = "\n".join(
            [f"Model: {model}\nError: {results[model]['stderr']}\n" for model in failed_models]
        )
        pytest.fail(f"Failed Hailo8L REID models on Hailo 8:\n{failure_details}")


def test_hailo8l_on_hailo8_tiling(h8l_tester):
    """Test Hailo8L models on Hailo 8 for tiling pipeline."""
    if h8l_tester.hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {h8l_tester.hailo_arch}")

    results = h8l_tester.run_pipeline_tests("tiling")

    failed_models = [model for model, result in results.items() if not result["success"]]
    if failed_models:
        failure_details = "\n".join(
            [f"Model: {model}\nError: {results[model]['stderr']}\n" for model in failed_models]
        )
        pytest.fail(f"Failed Hailo8L tiling models on Hailo 8:\n{failure_details}")


def test_hailo8l_on_hailo8_tiling_configurations(h8l_tester):
    """Test Hailo8L tiling models with basic configurations on Hailo 8."""
    if h8l_tester.hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {h8l_tester.hailo_arch}")

    # Test a subset of models with basic tiling configurations
    test_models = ["yolov6n", "ssd_mobilenet_v1_visdrone"]
    test_configurations = [
        # Default configuration (single-scale)
        {"name": "default", "args": []},
        # General detection configuration (multi-scale)
        {"name": "general_detection", "args": ["--general-detection"]},
    ]

    all_results = {}

    for model in test_models:
        model_results = {}
        for config in test_configurations:
            config_name = config["name"]
            extra_args = config["args"]

            logger.info(f"Testing tiling {model} with {config_name} configuration")
            stdout, stderr, success = h8l_tester.run_model("tiling", model, extra_args)

            model_results[config_name] = {
                "success": success,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
            }

            if success:
                logger.info(f"✓ {model} with {config_name}")
            else:
                logger.error(f"✗ {model} with {config_name}")

        all_results[model] = model_results

    # Check results
    failed_tests = []
    for model, configs in all_results.items():
        for config_name, result in configs.items():
            if not result["success"]:
                failed_tests.append(f"{model}/{config_name}: {result['stderr']}")

    if failed_tests:
        failure_summary = "\n".join(failed_tests)
        pytest.fail(f"Failed Hailo8L tiling configuration tests on Hailo 8:\n{failure_summary}")


def test_hailo8l_on_hailo8_comprehensive(h8l_tester):
    """Comprehensive test that runs all Hailo8L models on Hailo 8 for all supported pipeline types."""
    if h8l_tester.hailo_arch != HAILO8_ARCH:
        pytest.skip(f"Skipping Hailo-8L model test on {h8l_tester.hailo_arch}")

    logger.info("Running comprehensive Hailo8L model test on Hailo 8")

    all_results = {}
    total_tests = 0
    total_passed = 0

    # Test each pipeline type
    for pipeline_type in h8l_tester.h8l_models.keys():
        results = h8l_tester.run_pipeline_tests(pipeline_type)
        all_results[pipeline_type] = results

        for model, result in results.items():
            total_tests += 1
            if result["success"]:
                total_passed += 1

    # Generate summary report
    logger.info("\nHailo8L on Hailo 8 Comprehensive Test Summary:")
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Passed: {total_passed}")
    logger.info(f"Failed: {total_tests - total_passed}")

    # Log detailed results by pipeline type
    for pipeline_type, results in all_results.items():
        failed_models = [model for model, result in results.items() if not result["success"]]
        passed_models = [model for model, result in results.items() if result["success"]]
        logger.info(f"{pipeline_type}: {len(passed_models)}/{len(results)} models passed")
        if failed_models:
            logger.error(f"{pipeline_type} failed models: {failed_models}")

    # Assert overall success
    if total_passed < total_tests:
        failed_details = []
        for pipeline_type, results in all_results.items():
            for model, result in results.items():
                if not result["success"]:
                    failed_details.append(f"{pipeline_type}/{model}: {result['stderr']}")

        failure_summary = "\n".join(failed_details)
        pytest.fail(
            f"Hailo8L on Hailo 8 comprehensive testing failed. {total_passed}/{total_tests} tests passed.\n\nFailures:\n{failure_summary}"
        )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
