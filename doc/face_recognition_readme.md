# Face Recognition System

This project is a face recognition system built using Python, GStreamer, LanceDB, Gradio, FastRTC and FiftyOne.

This project is moderately advanced and is recommended for use after gaining some experience with the "Basic Pipelines."

The system supports real-time face recognition using GStreamer pipelines and the Hailo neural network AI accelerator.

It can train the known persons' catalog from a provided directory with images of persons (train mode below).

The information is managed in a local database optimized for storing and indexing AI embeddings, called LanceDB. This is a significant improvement over the commonly used static string-based files, such as JSON.

The system has several modes

The system provides an optional web interface, powered by the well-known FiftyOne platform (Python package installation required), for managing face recognition data, including visualizing embeddings and adding, updating, or deleting persons and their associated images. The web interface runs on localhost and interacts with the local LanceDB database.

In addition, the db_handler.py module provides a custom API for interactions with the LanceDB database for fine-grained DB management.

One of the key features of the system is the run mode with the --visualize flag, which provides a live display of the current catalog as 2D embeddings. With every new face recognition, the system adds it as a 2D embedding to the display, offering natural visibility into the recognition process and an intuitive understanding of why a face was recognized as someone or not.

For demonstration purposes, the current application demonstrates sending Telegram notifications via a bot when a person is detected. To enbale this feature, Telebot package is required but not installed by default, so you need to install it separately. Please note that a bot token and chat ID must be provided. In their absence, the function will simply do nothing. Please refer to Telegram guides on how to set up a bot.

Below is an example of the face recognition system in action:

![Example](images/example_image.png "Example")

This image demonstrates the live visualization of embeddings during the recognition process, showcasing how the system identifies and maps faces in real-time.

For each face detection, there is a confidence level, followed by another confidence level for the recognition itself. If there is a match with one of the faces in the database, the name is displayed; otherwise, the text "Unknown" is shown.

Face recognition confidence is per person record in the database, initiated with a default value (0.3) and can be manually modified either via the FiftyOne web interface or the db_handler.py API.


## Prerequisites

- Python 3.8+
- Pipenv or virtualenv for dependency management
- Required Python libraries (see `requirements.txt`)
- GStreamer installed on the system
- LanceDB installed for database management


## Installation

TODO: Based on new infra

## Usage

### Face Recognition Options Flow

![Face Recognition Options Flow](images/Face_detection.png "Face Recognition Architecture")

## Web Interface

   ```bash
   python embedding_visualizer.py
   ```
Open the interface on: http://localhost:5151/ (When executed from an IDE such as VS Code, it will automatically redirect to the browser).

Please refer to the https://voxel51.com/fiftyone/ guide for more details about using the interface.

---

## Telegram Notifications

- Configure the `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` in `app_db.py` to enable Telegram notifications.
- Notifications are sent when a face is detected, with an image and confidence score.

---

## Acknowledgments

- [GStreamer](https://gstreamer.freedesktop.org/)
- [LanceDB](https://lancedb.github.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Voxel51](https://voxel51.com/fiftyone/)
- [Gradio](https://www.gradio.app/)
- [FastRTC](https://fastrtc.org/)

## Appendix: Brief Explanation of the Code Architecture and Design

