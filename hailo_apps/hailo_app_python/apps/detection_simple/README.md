# Detection Simple Application

![Detection Simple Example](../../../../doc/images/detection.gif)

#### Run the detection simple example:
```bash
hailo-detection-simple
```
To close the application, press `Ctrl+C`.

This is lightweight version of the detection example, mainly focusing on demonstrating Hailo performance while minimizing CPU load. The internal GStreamer video processing pipeline is simplified by minimizing video processing tasks, and the YOLOv6 Nano model is used.

The application will detect and classify various objects.

For more details, pleasee see the full detection application: [Full detection application](../../apps/detection/README.md)

#### Running with Raspberry Pi Camera input:
```bash
hailo-detection-simple --input rpi
```

#### Running with USB camera input (webcam):
There are 2 ways:

Specify the argument `--input` to `usb`:
```bash
hailo-detection-simple --input usb
```

This will automatically detect the available USB camera (if multiple are connected, it will use the first detected).

Second way:

Detect the available camera using this script:
```bash
get-usb-camera
```
Run example using USB camera input - Use the device found by the previous script:
```bash
hailo-detection-simple --input /dev/video<X>
```

For additional options, execute:
```bash
hailo-detection-simple --help
```

#### Running as Python script

For examples: 
```bash
python detection_simple.py --input usb
```