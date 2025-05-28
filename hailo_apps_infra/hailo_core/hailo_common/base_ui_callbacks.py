import threading
import queue

FRAME_TIMEOUT = 0.5

class BaseUICallbacks:
    def __init__(self, pipeline):
        self.FRAME_TIMEOUT = FRAME_TIMEOUT
        self.stop_event = threading.Event()  # create a stop event to signal threads to stop
        self.pipeline = pipeline

    def process_frames(self):
        """
        Function to process frames from the queue at high FPS.
        """
        while not self.stop_event.is_set():
            try:
                yield self.pipeline.webrtc_frames_queue.get(timeout=self.FRAME_TIMEOUT)  # Get a frame from the queue (blocking)
            except queue.Empty:  # No frame available in the queue
                if self.stop_event.is_set():
                    break