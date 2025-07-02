
import mss
import cv2
import numpy as np
import pyttsx3
import time
from transformers import pipeline
from PIL import Image
import torch
from pyautogui import hotkey
from utils.config import get_close_tab_action
import threading
import webbrowser

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
loading_start_time = None
NSFW_THRESHOLD = 0.5  # Default threshold
MOTIVATIONAL_URL = "https://www.youtube.com/shorts/8SVZLF75P2M"
ENABLE_REDIRECT = True

def set_nsfw_threshold(threshold):
    global NSFW_THRESHOLD
    NSFW_THRESHOLD = float(threshold)
    print(f"NSFW threshold updated to: {NSFW_THRESHOLD}")

def load_model(progress_callback=None):
    global classifier, loading_complete, loading_error, loading_start_time
    with model_lock:
        if loading_complete or classifier is not None:
            print("Model already loaded or loading complete, skipping.")
            if progress_callback:
                progress_callback(100, "Model already loaded!")
            return
        print(f"Loading model (attempt: {getattr(load_model, 'call_count', 0) + 1})")
        load_model.call_count = getattr(load_model, 'call_count', 0) + 1
        loading_start_time = time.time()
        try:
            if progress_callback:
                progress_callback(0, "Starting model load...")
            print(f"Attempting to load model from: {MODEL_NAME}, device: {device}")
            classifier = pipeline("image-classification", model=MODEL_NAME, device=device, use_fast=True)  # Removed cache_dir
            print(f"Classifier initialized: {classifier is not None}")
            if progress_callback:
                progress_callback(50, "Model half-loaded...")
            print(f"Model loaded in {time.time() - loading_start_time:.2f} seconds!")
            loading_complete = True
            if progress_callback:
                progress_callback(100, "Model loaded successfully!")
        except Exception as e:
            loading_error = str(e)
            print(f"Failed to load model: {e}")
            classifier = None  # Ensure classifier is None on failure
            if progress_callback:
                progress_callback(100, f"Error: {e}")

def has_adult_content(image):
    global classifier, loading_error, NSFW_THRESHOLD
    print(f"Checking adult content, classifier: {classifier is not None}, threshold: {NSFW_THRESHOLD}")
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
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        if img.shape[2] == 4:  # RGBA
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

def speak_alert(content_type, score):
    message = f"Warning: Detected {content_type} with confidence {score:.2f}. Please review the content."
    print(message)
    hotkey(*get_close_tab_action())
    time.sleep(0.1)
    # engine.say(message)
    # engine.runAndWait()
    if ENABLE_REDIRECT and MOTIVATIONAL_URL:
        try:
            webbrowser.get("chrome").open_new_tab(MOTIVATIONAL_URL)
        except Exception:
            webbrowser.open_new_tab(MOTIVATIONAL_URL)

def main():
    global classifier, loading_complete
    print("Starting screen monitoring for adult content...")
    while True:
        if not classifier:
            print("Model not loaded yet.")
            time.sleep(1)
            continue
        screen_img = capture_screen()
        is_adult, content_type, score = has_adult_content(screen_img)
        if is_adult:
            speak_alert(content_type, score)
        time.sleep(1)

def stop_monitoring():
    print("Stopping monitoring...")