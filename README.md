# Hailo Applications Infrastructure

This repository provides the core infrastructure and pipelines required to run Hailo applications. It includes three key application pipelines:
- **Object Detection**
- **Pose Estimation**
- **Instance Segmentation**

Requirements
------------

- hailo_platform==4.19.0
- Pyhailort

## Using the Repository as a Pip Package
-----------------------------
To install the package, ensure you are inside a virtual environment with Pyhailort installed. Then, run the following command:
```shell script
pip install git+https://github.com/hailo-ai/hailo-apps-infra.git
```
This will install the Hailo Applications Infrastructure package directly from the repository.


## Running the Pipelines
--------------------

1. Clone the repository:
    ```shell script
    git clone https://github.com/ronithailo/hailo-apps-infra.git
            
    cd hailo-apps-infra
    ```

2. Install the Python Package

    We recommend running it within a virtual environment.
    ```shell script
    pip install -v -e .
    ```
    This will install the package in editable mode, allowing you to make changes to the codebase and use them immediately without reinstalling.

3. Running Detection Pipeline:
    ```shell script
    python hailo_apps_infra/detection_pipeline.py 
    ```
    ![Example](./resources/detection.gif)
4. Running Pose Estimation Pipeline:
    ```shell script
    python hailo_apps_infra/pose_estimation_pipeline.py
    ```
    ![Example](./resources/pose_estimation.gif)
5. Running Instance Segmentation Pipeline:
    ```shell script
    python hailo_apps_infra/instance_segmentation_pipeline.py
    ```
    ![Example](./resources/instance_segmentation.gif)
## Pipeline Options
For more information about the available options, run any of the pipeline scripts with the -h flag:
    ```shell script
    python hailo_apps_infra/detection_pipeline.py -h
    ```
```shell script
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        Input source. Can be a file, USB or RPi camera (CSI camera module). For RPi camera use '-i rpi' (Still in Beta). Defaults to example video resources/detection0.mp4
  --use-frame, -u       Use frame from the callback function
  --show-fps, -f        Print FPS on sink
  --arch {hailo8,hailo8l}
                        Specify the Hailo architecture (hailo8 or hailo8l). Default is None , app will run check.
  --hef-path HEF_PATH   Path to HEF file
  --disable-sync        Disables display sink sync, will run as fast as possible. Relevant when using file source.
  --dump-dot            Dump the pipeline graph to a dot file pipeline.dot
```

License
----------
The infrastructure is released under the MIT license. Please see the https://github.com/hailo-ai/hailo-BEV/blob/main/LICENSE file for more information.


Disclaimer
----------
This code infrastructure is provided by Hailo solely on an “AS IS” basis and “with all faults”. No responsibility or liability is accepted or shall be imposed upon Hailo regarding the accuracy, merchantability, completeness or suitability of the code infrastructure. Hailo shall not have any liability or responsibility for errors or omissions in, or any business decisions made by you in reliance on this code infrastructure or any part of it. If an error occurs when running this infrastructure, please open a ticket in the "Issues" tab.

This infrastructure was tested on specific versions and we can only guarantee the expected results using the exact version mentioned above on the exact environment. The infrastructure might work for other versions, other environment or other HEF file, but there is no guarantee that it will.