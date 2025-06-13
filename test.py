from transformers import pipeline
classifier = pipeline("image-classification", model="Falconsai/nsfw_image_detection", device="cpu", use_fast=True)
print("Model loaded successfully!")