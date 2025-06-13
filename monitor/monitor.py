import mss
import cv2
import numpy as np
import pyttsx3
import time
from transformers import pipeline
from PIL import Image
import torch
from pyautogui import hotkey
from utils import get_close_tab_action
import threading

# Set device to CPU
device = torch.device("cpu")

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Model loading variables
MODEL_NAME = "Falconsai/nsfw_image_detection"
classifier = None
loading_complete = False
loading_error = None
model_lock = threading.Lock()

def load_model(progress_callback=None):
    """Load the NSFW model with progress feedback."""
    global classifier, loading_complete, loading_error
    with model_lock:
        print(f"Loading model (attempt: {getattr(load_model, 'call_count', 0) + 1})")
        load_model.call_count = getattr(load_model, 'call_count', 0) + 1
        if classifier is not None:
            print("Model already loaded, skipping.")
            if progress_callback:
                progress_callback(100, "Model already loaded!")
            return
        try:
            if progress_callback:
                progress_callback(0, "Starting model load...")
            classifier = pipeline("image-classification", model=MODEL_NAME, device=device, use_fast=True)
            if progress_callback:
                progress_callback(50, "Model half-loaded...")
            print("Successfully loaded model!")
            loading_complete = True
            if progress_callback:
                progress_callback(100, "Model loaded successfully!")
        except Exception as e:
            loading_error = str(e)
            print(f"Failed to load model: {e}")
            if progress_callback:
                progress_callback(100, f"Error: {e}")

# Threshold for NSFW detection
NSFW_THRESHOLD = 0.2

def has_adult_content(image):
    """Check if an image contains adult content."""
    global classifier, loading_error
    if not classifier:
        return False, None, 0
    try:
        if isinstance(image, np.ndarray):
            img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        elif isinstance(image, Image.Image):
            img_pil = image.convert("RGB")
        else:
            raise ValueError("Input must be a NumPy array or PIL.Image")
        
        results = classifier(img_pil)
        print("Prediction scores:", {r['label']: f"{r['score']:.4f}" for r in results})
        
        nsfw_result = next((r for r in results if r['label'] == 'nsfw'), {'score': 0})
        nsfw_score = nsfw_result['score']
        is_adult = nsfw_score > NSFW_THRESHOLD
        content_type = "NSFW" if is_adult else None
        
        print(f"Adult content check: {is_adult}, Type: {content_type}, Score: {nsfw_score:.4f}")
        return is_adult, content_type, nsfw_score
    except Exception as e:
        print(f"Error in adult content detection: {e}")
        return False, None, 0

def capture_screen():
    """Capture the entire screen using mss and convert to OpenCV format."""
    with mss.mss() as sct:
        if not hasattr(capture_screen, 'monitors_printed'):
            print("Available monitors:", sct.monitors)
            capture_screen.monitors_printed = True
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        print(f"Monitor: width={screenshot.width}, height={screenshot.height}")
        print(f"RGB data size: {len(screenshot.rgb)}")
        total_pixels = screenshot.width * screenshot.height
        channels = len(screenshot.rgb) // total_pixels
        if channels not in [3, 4]:
            raise ValueError(f"Unexpected number of channels: {channels}")
        print(f"Detected channels: {channels}")
        img = np.frombuffer(screenshot.rgb, dtype=np.uint8)
        img = img.reshape((screenshot.height, screenshot.width, channels))
        if channels == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img

def speak_alert(content_type, score):
    """Speak an alert when adult content is detected."""
    message = f"Warning: Detected {content_type} with confidence {score:.2f}. Please review the content."
    print(message)
    hotkey(*get_close_tab_action())
    time.sleep(0.1)
    # engine.say(message)
    # engine.runAndWait()

def main():
    """Monitor screen for adult content in real-time."""
    global classifier, loading_complete
    print("Starting screen monitoring for adult content...")
    try:
        while getattr(main, 'running', True):
            if not classifier:
                print("Model not loaded yet.")
                time.sleep(1)
                continue
            screen_img = capture_screen()
            is_adult, content_type, score = has_adult_content(screen_img)
            if is_adult:
                speak_alert(content_type, score)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
    except Exception as e:
        print(f"Error in monitoring loop: {e}")
    finally:
        main.running = False

def stop_monitoring():
    """Stop the monitoring loop."""
    main.running = False