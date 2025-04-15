import pytest
from hailo_apps_infra.common.test_utils import (
    get_device_architecture,
    get_compatible_hefs,
    get_available_video_inputs,
    is_rpi_camera_available,
    run_pipeline_test
)
#add default runs as the regular one , keep the exterme and edge cases to the stability and the CI
# find a way to have the pipelines as config 
PIPELINE_CONFIG = [
    ("hailo_apps_infra.core.detection_pipeline", "detection"),
    ("hailo_apps_infra.core.detection_pipeline_simple", "detection_simple"),
    ("hailo_apps_infra.core.pose_estimation_pipeline", "pose"),
    ("hailo_apps_infra.core.instance_segmentation_pipeline", "segmentation"),
    ("hailo_apps_infra.core.depth_pipeline", "depth")
]

@pytest.mark.parametrize("pipeline_module,model_type", PIPELINE_CONFIG)
def test_all_hefs_with_file_input(pipeline_module, model_type):
    _, hailo_arch = get_device_architecture()
    hefs = get_compatible_hefs(hailo_arch, model_type)
    inputs = get_available_video_inputs()
    video_file = inputs['file'][0] if 'file' in inputs and inputs['file'] else "resources/video/example.mp4"

    for hef in hefs:
        assert run_pipeline_test(
            pipeline_module=pipeline_module,
            hef_path=hef,
            input_source=video_file,
            input_type="file"
        ), f"{pipeline_module} failed with {hef} using file input"


@pytest.mark.parametrize("pipeline_module,model_type", PIPELINE_CONFIG)
def test_all_hefs_with_usb_input(pipeline_module, model_type):
    _, hailo_arch = get_device_architecture()
    hefs = get_compatible_hefs(hailo_arch, model_type)
    inputs = get_available_video_inputs()

    if 'usb' not in inputs or not inputs['usb']:
        pytest.skip("No USB camera input detected")

    usb_source = inputs['usb'][0]

    for hef in hefs:
        # We do not assert failure here, as USB may behave inconsistently
        run_pipeline_test(
            pipeline_module=pipeline_module,
            hef_path=hef,
            input_source=usb_source,
            input_type="usb"
        )


@pytest.mark.parametrize("pipeline_module,model_type", PIPELINE_CONFIG)
def test_all_hefs_with_rpi_input(pipeline_module, model_type):
    if not is_rpi_camera_available():
        pytest.skip("RPi camera not available")

    _, hailo_arch = get_device_architecture()
    hefs = get_compatible_hefs(hailo_arch, model_type)

    for hef in hefs:
        assert run_pipeline_test(
            pipeline_module=pipeline_module,
            hef_path=hef,
            input_source="rpi",
            input_type="rpi"
        ), f"{pipeline_module} failed with {hef} using RPi camera"
    # Note: RPi camera tests may be skipped if the camera is not available