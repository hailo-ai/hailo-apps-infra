#!/bin/bash

# Set the resource directory
RESOURCE_DIR="./resources"
mkdir -p "$RESOURCE_DIR"

# Define download function with file existence check and retries
download_model() {
  local url=$1
  local file_name=$(basename "$url")

  # Check if the file is scdepthv3.hef and part of H8L_HEFS
  if [[ "$url" == *"scdepthv3.hef" && "$url" == *"hailo8l"* ]]; then
    file_name="scdepthv3_h8l.hef"
  fi

  # Check if the file is yolov11m.hef and part of H8L_HEFS
  if [[ "$url" == *"yolov11s.hef" && "$url" == *"hailo8l"* ]]; then
    file_name="yolov11s_h8l.hef"
  fi

  local file_path="$RESOURCE_DIR/$file_name"

  if [ ! -f "$file_path" ]; then
    echo "Downloading $file_name..."
    wget -q --show-progress "$url" -O "$file_path" || {
      echo "Failed to download $file_name after multiple attempts."
      exit 1
    }
  else
    echo "File $file_name already exists in $RESOURCE_DIR. Skipping download."
  fi
}

# Define all URLs in arrays
H8_HEFS=(
  "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.13.0/hailo8/yolov8m_pose.hef"
  "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.13.0/hailo8/yolov5m_seg.hef"
  "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.13.0/hailo8/yolov8m.hef"
  "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/scdepthv3.hef"
  "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov11m.hef"
)

H8L_HEFS=(
  "https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/hefs/h8l_rpi/yolov8s_h8l.hef"
  "https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/hefs/h8l_rpi/yolov5n_seg_h8l_mz.hef"
  "https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/hefs/h8l_rpi/yolov8s_pose_h8l.hef"
  "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/scdepthv3.hef"
  "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov11s.hef"
)

VIDEOS=(
  "https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/video/example.mp4"
)

# If --all flag is provided, download everything in parallel
if [ "$1" == "--all" ]; then
  echo "Downloading all models and video resources..."
  for url in "${H8_HEFS[@]}" "${H8L_HEFS[@]}" "${VIDEOS[@]}"; do
    download_model "$url" &
  done
else
  if [ "$DEVICE_ARCHITECTURE" == "HAILO8L" ]; then
    echo "Downloading HAILO8L models..."
    for url in "${H8L_HEFS[@]}"; do
      download_model "$url" &
    done
  elif [ "$DEVICE_ARCHITECTURE" == "HAILO8" ]; then
    echo "Downloading HAILO8 models..."
    for url in "${H8_HEFS[@]}"; do
      download_model "$url" &
    done
  fi
fi

# Download additional videos
for url in "${VIDEOS[@]}"; do
  download_model "$url" &
done

# Wait for all background downloads to complete
wait

echo "All downloads completed successfully!"
