import os

def get_source_type(input_source):
    # This function will return the source type based on the input source
    # return values can be "file", "mipi" or "usb"
    if input_source.startswith("/dev/video"):
        return 'usb'
    elif input_source.startswith("rpi"):
        return 'rpi'
    elif input_source.startswith("libcamera"): # Use libcamerasrc element, not suggested
        return 'libcamera'
    elif input_source.startswith('0x'):
        return 'ximage'
    else:
        return 'file'

def QUEUE(name, max_size_buffers=3, max_size_bytes=0, max_size_time=0, leaky='no'):
    """
    Creates a GStreamer queue element string with the specified parameters.

    Args:
        name (str): The name of the queue element.
        max_size_buffers (int, optional): The maximum number of buffers that the queue can hold. Defaults to 3.
        max_size_bytes (int, optional): The maximum size in bytes that the queue can hold. Defaults to 0 (unlimited).
        max_size_time (int, optional): The maximum size in time that the queue can hold. Defaults to 0 (unlimited).
        leaky (str, optional): The leaky type of the queue. Can be 'no', 'upstream', or 'downstream'. Defaults to 'no'.

    Returns:
        str: A string representing the GStreamer queue element with the specified parameters.
    """
    q_string = f'queue name={name} leaky={leaky} max-size-buffers={max_size_buffers} max-size-bytes={max_size_bytes} max-size-time={max_size_time} '
    return q_string

def SOURCE_PIPELINE(video_source, video_width=640, video_height=640, video_format='RGB', name='source', no_webcam_compression=False):
    """
    Creates a GStreamer pipeline string for the video source.

    Args:
        video_source (str): The path or device name of the video source.
        video_width (int, optional): The width of the video. Defaults to 640.
        video_height (int, optional): The height of the video. Defaults to 640.
        video_format (str, optional): The video format. Defaults to 'RGB'.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'source'.

    Returns:
        str: A string representing the GStreamer pipeline for the video source.
    """
    source_type = get_source_type(video_source)

    if source_type == 'usb':
        if no_webcam_compression:
            source_element = (
                f'v4l2src device={video_source} name={name} ! '
                'video/x-raw, format=RGB, width=640, height=480 ! '
            )
        else:
            # Use compressed format for webcam
            source_element = (
                f'v4l2src device={video_source} name={name} ! image/jpeg, framerate=30/1 ! '
                f'{QUEUE(name=f"{name}_queue_decode")} ! '
                f'decodebin name={name}_decodebin ! '
            )
    elif source_type == 'rpi':
        source_element = (
            f'appsrc name=app_source is-live=true leaky-type=downstream max-buffers=3 ! '
            'videoflip name=videoflip video-direction=horiz ! '
            f'video/x-raw, format={video_format}, width={video_width}, height={video_height} ! '
        )
    elif source_type == 'libcamera':
        source_element = (
            f'libcamerasrc name={name} ! '
            f'video/x-raw, format={video_format}, width=1536, height=864 ! '
        )
    elif source_type == 'ximage':
        source_element = (
            f'ximagesrc xid={video_source} ! '
            f'{QUEUE(name=f"{name}queue_scale_")} ! '
            f'videoscale ! '
        )
    else:
        source_element = (
            f'filesrc location="{video_source}" name={name} ! '
            f'{QUEUE(name=f"{name}_queue_decode")} ! '
            f'decodebin name={name}_decodebin ! '
        )
    source_pipeline = (
        f'{source_element} '
        f'{QUEUE(name=f"{name}_scale_q")} ! '
        f'videoscale name={name}_videoscale n-threads=2 ! '
        f'{QUEUE(name=f"{name}_convert_q")} ! '
        f'videoconvert n-threads=3 name={name}_convert qos=false ! '
        f'video/x-raw, pixel-aspect-ratio=1/1, format={video_format}, width={video_width}, height={video_height} ! '
    )

    return source_pipeline

def INFERENCE_PIPELINE(hef_path, post_process_so, batch_size=1, config_json=None, post_function_name=None, additional_params='', name='inference'):
    """
    Creates a GStreamer pipeline string for inference and post-processing using a user-provided shared object file.
    This pipeline includes videoscale and videoconvert elements to convert the video frame to the required format.
    The format and resolution are automatically negotiated based on the HEF file requirements.

    Args:
        hef_path (str): The path to the HEF file.
        post_process_so (str): The path to the post-processing shared object file.
        batch_size (int, optional): The batch size for the hailonet element. Defaults to 1.
        config_json (str, optional): The path to the configuration JSON file. If None, no configuration is added. Defaults to None.
        post_function_name (str, optional): The name of the post-processing function. If None, no function name is added. Defaults to None.
        additional_params (str, optional): Additional parameters for the hailonet element. Defaults to ''.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'inference'.

    Returns:
        str: A string representing the GStreamer pipeline for inference.
    """
    # Configure config path if provided
    if config_json is not None:
        config_str = f' config-path={config_json} '
    else:
        config_str = ''

    # Configure function name if provided
    if post_function_name is not None:
        function_name_str = f' function-name={post_function_name} '
    else:
        function_name_str = ''

    # Construct the inference pipeline string
    inference_pipeline = (
        f'{QUEUE(name=f"{name}_scale_q")} ! '
        f'videoscale name={name}_videoscale n-threads=2 qos=false ! '
        f'{QUEUE(name=f"{name}_convert_q")} ! '
        f'video/x-raw, pixel-aspect-ratio=1/1 ! '
        f'videoconvert name={name}_videoconvert n-threads=2 ! '
        f'{QUEUE(name=f"{name}_hailonet_q")} ! '
        f'hailonet name={name}_hailonet hef-path={hef_path} batch-size={batch_size} {additional_params} force-writable=true ! '
        f'{QUEUE(name=f"{name}_hailofilter_q")} ! '
        f'hailofilter name={name}_hailofilter so-path={post_process_so} {config_str} {function_name_str} qos=false '
    )

    return inference_pipeline

def INFERENCE_PIPELINE_WRAPPER(inner_pipeline, bypass_max_size_buffers=20, name='inference_wrapper'):
    """
    Creates a GStreamer pipeline string that wraps an inner pipeline with a hailocropper and hailoaggregator.
    This allows to keep the original video resolution and color-space (format) of the input frame.
    The inner pipeline should be able to do the required conversions and rescale the detection to the original frame size.

    Args:
        inner_pipeline (str): The inner pipeline string to be wrapped.
        bypass_max_size_buffers (int, optional): The maximum number of buffers for the bypass queue. Defaults to 20.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'inference_wrapper'.

    Returns:
        str: A string representing the GStreamer pipeline for the inference wrapper.
    """
    # Get the directory for post-processing shared objects
    tappas_post_process_dir = os.environ.get('TAPPAS_POST_PROC_DIR', '')
    whole_buffer_crop_so = os.path.join(tappas_post_process_dir, 'cropping_algorithms/libwhole_buffer.so')

    # Construct the inference wrapper pipeline string
    inference_wrapper_pipeline = (
        f'{QUEUE(name=f"{name}_input_q")} ! '
        f'hailocropper name={name}_crop so-path={whole_buffer_crop_so} function-name=create_crops use-letterbox=true resize-method=inter-area internal-offset=true '
        f'hailoaggregator name={name}_agg '
        f'{name}_crop. ! {QUEUE(max_size_buffers=bypass_max_size_buffers, name=f"{name}_bypass_q")} ! {name}_agg.sink_0 '
        f'{name}_crop. ! {inner_pipeline} ! {name}_agg.sink_1 '
        f'{name}_agg. ! {QUEUE(name=f"{name}_output_q")} '
    )

    return inference_wrapper_pipeline

def DISPLAY_PIPELINE(video_sink='xvimagesink', sync='true', show_fps='false', name='hailo_display'):
    """
    Creates a GStreamer pipeline string for displaying the video.
    It includes the hailooverlay plugin to draw bounding boxes and labels on the video.

    Args:
        video_sink (str, optional): The video sink element to use. Defaults to 'xvimagesink'.
        sync (str, optional): The sync property for the video sink. Defaults to 'true'.
        show_fps (str, optional): Whether to show the FPS on the video sink. Should be 'true' or 'false'. Defaults to 'false'.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'hailo_display'.

    Returns:
        str: A string representing the GStreamer pipeline for displaying the video.
    """
    # Construct the display pipeline string
    display_pipeline = (
        f'{QUEUE(name=f"{name}_hailooverlay_q")} ! '
        f'hailooverlay name={name}_hailooverlay ! '
        f'{QUEUE(name=f"{name}_videoconvert_q")} ! '
        f'videoconvert name={name}_videoconvert n-threads=2 qos=false ! '
        f'{QUEUE(name=f"{name}_q")} ! '
        f'fpsdisplaysink name={name} video-sink={video_sink} sync={sync} text-overlay={show_fps} signal-fps-measurements=true '
    )

    return display_pipeline

def USER_CALLBACK_PIPELINE(name='identity_callback'):
    """
    Creates a GStreamer pipeline string for the user callback element.

    Args:
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'identity_callback'.

    Returns:
        str: A string representing the GStreamer pipeline for the user callback element.
    """
    # Construct the user callback pipeline string
    user_callback_pipeline = (
        f'{QUEUE(name=f"{name}_q")} ! '
        f'identity name={name} '
    )

    return user_callback_pipeline

def TRACKER_PIPELINE(class_id, kalman_dist_thr=0.8, iou_thr=0.9, init_iou_thr=0.7, keep_new_frames=2, keep_tracked_frames=15, keep_lost_frames=2, keep_past_metadata=False, qos=False, name='hailo_tracker'):
    """
    Creates a GStreamer pipeline string for the HailoTracker element.
    Args:
        class_id (int): The class ID to track. Default is -1, which tracks across all classes.
        kalman_dist_thr (float, optional): Threshold used in Kalman filter to compare Mahalanobis cost matrix. Closer to 1.0 is looser. Defaults to 0.8.
        iou_thr (float, optional): Threshold used in Kalman filter to compare IOU cost matrix. Closer to 1.0 is looser. Defaults to 0.9.
        init_iou_thr (float, optional): Threshold used in Kalman filter to compare IOU cost matrix of newly found instances. Closer to 1.0 is looser. Defaults to 0.7.
        keep_new_frames (int, optional): Number of frames to keep without a successful match before a 'new' instance is removed from the tracking record. Defaults to 2.
        keep_tracked_frames (int, optional): Number of frames to keep without a successful match before a 'tracked' instance is considered 'lost'. Defaults to 15.
        keep_lost_frames (int, optional): Number of frames to keep without a successful match before a 'lost' instance is removed from the tracking record. Defaults to 2.
        keep_past_metadata (bool, optional): Whether to keep past metadata on tracked objects. Defaults to False.
        qos (bool, optional): Whether to enable QoS. Defaults to False.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'hailo_tracker'.
    Note:
        For a full list of options and their descriptions, run `gst-inspect-1.0 hailotracker`.
    Returns:
        str: A string representing the GStreamer pipeline for the HailoTracker element.
    """
    # Construct the tracker pipeline string
    tracker_pipeline = (
        f'hailotracker name={name} class-id={class_id} kalman-dist-thr={kalman_dist_thr} iou-thr={iou_thr} init-iou-thr={init_iou_thr} '
        f'keep-new-frames={keep_new_frames} keep-tracked-frames={keep_tracked_frames} keep-lost-frames={keep_lost_frames} keep-past-metadata={keep_past_metadata} qos={qos} ! '
        f'{QUEUE(name=f"{name}_q")} '
    )
    return tracker_pipeline
