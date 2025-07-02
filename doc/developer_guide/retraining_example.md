## Using YOLOv8 Retraining Docker

In this example, we’re going to retrain the model to detect barcodes, using the barcode-detector dataset from Kaggle. After the retraining process, we’re going to convert the model to HEF and test it on the Raspberry Pi 5 AI Kit.

### This tutorial was created on a development machine with the following specifications

**Hardware**:
- CPU: Intel i7-6850K
- GPU: RTX 4080

**Software**:
- OS: Ubuntu 20.04
- Hailo DFC version: 3.27.0
- Hailo Model-Zoo: 2.11.0

### On the development machine

1. Install the Hailo AI SW-Suite from the [Developer Zone](https://hailo.ai/developer-zone/software-downloads/). Alternatively, you can download and install the DFC and the model-zoo into the same virtual environment.
2. Follow the instructions on the YOLOv8 retraining page: [YOLOv8 Retraining](https://github.com/hailo-ai/hailo_model_zoo/tree/833ae6175c06dbd6c3fc8faeb23659c9efaa2dbe/training/yolov8)
3. Note: In this example, we added a volume mount named `data` to the Docker container.
4. Download the [barcode-detector](https://www.kaggle.com/datasets/kushagrapandya/barcode-detection) dataset from Kaggle. Ensure that it is either mapped to the retraining Docker container or copied inside.

### Launch the retraining

On my RTX 4080, it took about 3 hours:

```bash
yolo detect train data=/data/barcode-detect/data.yaml model=yolov8s.pt name=retrain_yolov8s epochs=20 batch=8
```

After the final epoch has finished, you should see a message like this:
![final-epoch](../images/final-epoch.png)

### Validate the new checkpoint

```bash
yolo predict task=detect source=/data/barcode-detect/valid/images/05102009190_jpg.rf.e9661dd52bd50001b08e7a510978560b.jpg model=./runs/detect/retrain_yolov8s/weights/best.pt
```
Expected output:
![validate-model](../images/validate-model.png)
### Export the model to ONNX

```bash
yolo export model=/workspace/ultralytics/runs/detect/retrain_yolov8s/weights/best.pt imgsz=640 format=onnx opset=11
```

### Copy the ONNX to a directory mapped outside the Docker container

```bash
cp ./runs/detect/retrain_yolov8s/weights/best.onnx /data/barcode-detection.onnx
```

### Exit the Docker

### Convert the model to Hailo

Use the Hailo Model Zoo command (this can take up to 30 minutes):

```bash
hailomz compile yolov8s --ckpt=barcode-detection.onnx --hw-arch hailo8l --calib-path barcode-detect/test/images/ --classes 2 --performance
```
You should get a message like this: 
![successful-compilation](../images/successful-compilation.png)

### The yolov8s.hef file is now ready and can be used on the Raspberry Pi 5 AI Kit.

Load a custom model’s HEF using the `--hef-path` flag. Default labels are [COCO labels](https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/datasets/coco.yaml) (80 classes). For custom models with different labels, use the `--labels-path` flag to load your labels file (e.g., `/local_resources/barcode_labels.json`).

### Running the detection application with the example retrained model
To download the example retrained model, run the following command:
```bash
hailo-download-resources --group retrain
```

The default package installation downloads the network trained in the retraining example above, which can be used as a reference (including `/local_resources/barcode_labels.json`).

Here is an example of the command line required to run the application with the retrained custom model:
```bash
python hailo_apps/hailo_app_python/apps/detection/detection.py --labels-json resources/json/barcode_labels.json --hef-path resources/models/hailo8l/yolov8s-hailo8l-barcode.hef --input resources/videos/barcode.mp4
```

Example output:

![Example output](../images/barcode-example.png)
