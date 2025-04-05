import os
import cv2
import base64
import numpy as np
from flask import Flask, jsonify
from threading import Thread
import time
import subprocess
import requests
import logging
import json
from flask import request, jsonify
from datetime import datetime, timezone
import discord
import random

def get_iso_timestamp():
    return datetime.now(timezone.utc).isoformat()

API_URL=os.getenv("API_URL")
MODEL=os.getenv("MODEL")
STREAM_PROCESS_INTERVAL=int(os.getenv("STREAM_PROCESS_INTERVAL", 60))

def setup_logger():
    # Create a custom formatter that includes the thread name
    formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

    # Set up console handler with the formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Set up the logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Adjust log level as necessary
    logger.addHandler(console_handler)
    
    return logger

# Get the stream URL using yt_dlp
def get_stream_url(youtube_url):
    result = subprocess.run(
        ["yt-dlp", "-g", "-f", "best", youtube_url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip()


app = Flask(__name__)

# A dictionary to store stream info (title, URL) and detection state
streams = {}


def load_streams():
    index = 1
    while True:
        title = os.getenv(f"STREAM_{index}_TITLE")
        url = os.getenv(f"STREAM_{index}_URL")
        if not title or not url:
            break
        streams[title] = {
            "url": url,
            "bird_detected": False,
            "captured_frame": None,
            "captured_time": None,
            "last_bird_captured_frame": None,
            "last_bird_captured_time": None,
        }
        index += 1

# Capture a frame from the live stream
def capture_frame(stream_url):
    cap = cv2.VideoCapture(stream_url)
    ret, frame = cap.read()
    cap.release()
    return ret, frame

def frame_to_img(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    return buffer

# Convert an image to base64 string
def img_to_base64(img):
    return base64.b64encode(img).decode('utf-8')

def query_llava(base64_image):
    url = API_URL
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Is there a bird in this image? Just answer 'Yes' or 'No'.",
                "images": [base64_image]
            }
        ],
        "stream": True
    }

    response = requests.post(url, headers=headers, json=payload, stream=True)
    
    full_reply = ""
    for line in response.iter_lines():
        if line:
            try:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    full_reply += chunk["message"]["content"]
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
    
    return full_reply.strip()

# Process each stream and detect birds
def process_stream(title, yt_url):
    # Initial random delay to distribute load
    # time.sleep(random.randint(0, 10))
    logger = logging.getLogger()
    url = get_stream_url(yt_url)
    while True:
        logger.info("Capturing frame...")
        ret, frame = capture_frame(url)
        if ret is None:
            logger.info("No frame, break after 10s")
            time.sleep(10)
            break;
        img = frame_to_img(frame)
        frame_base64 = img_to_base64(img)
        logger.info("Querying LLaVA API...")
        answer = query_llava(frame_base64)
        logger.info(f"LLaVA response: {answer}")
        bird_detected = "Yes" in answer
        
        s=streams[title]
        was_detected_previously = s['bird_detected']
        s['bird_detected'] = bird_detected
        
        if bird_detected:
            logger.info("******* BIRD DETECTED YAY *********")
            ts = get_iso_timestamp()
            s['captured_frame'] = frame_base64
            s['captured_time'] = ts
            s['last_bird_captured_frame'] = frame_base64
            s['last_bird_captured_time'] = ts
        else:
            s['captured_frame'] = None
            s['captured_time'] = None

        notify = bird_detected and not was_detected_previously
        if notify:
            discord.postActivity(title, yt_url, img)

        now_gone = was_detected_previously and not bird_detected
        if now_gone:
            discord.postGone(title)
        
        # Sleep for a small time to simulate processing delay (adjust as needed)
        time.sleep(STREAM_PROCESS_INTERVAL)

# API to check which streams have detected birds
@app.route('/check', methods=['GET'])
def check_bird_detection():
    include_frame = request.args.get('include_frame', 'false').lower() == 'true'
    detected_streams = []
    
    for title, stream_data in streams.items():
        captured_frame = stream_data['captured_frame'] if include_frame else None
        last_bird_captured_frame = stream_data['last_bird_captured_frame'] if include_frame else None
        detected_streams.append({
            "current_time": get_iso_timestamp(),
            "title": title,
            "bird_detected": stream_data['bird_detected'],
            "captured_frame": captured_frame,
            "captured_time": stream_data['captured_time'],
            "last_bird_captured_frame": last_bird_captured_frame,
            "last_bird_captured_time": stream_data['last_bird_captured_time'],
            "url": stream_data['url']
        })
    
    return jsonify(detected_streams)

if __name__ == '__main__':
    logger = setup_logger()
    
    load_streams()
    logger.info(f"Loaded streams {streams}")
    
    # Start processing streams in background threads
    for title, stream_data in streams.items():
        Thread(target=process_stream, name=title, args=(title, stream_data["url"]), daemon=True).start()
    
    # Start Flask application
    app.run(debug=True, host="0.0.0.0", port=5000)

