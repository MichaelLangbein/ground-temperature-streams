from flask import Flask, request
from google.cloud import pubsub_v1
from google.api_core.retry import Retry
from utils import Bbox, TimeRange
from downloader import downloadData
import datetime
import base64
import logging
import os
import json


# Getting environment variables
usgsUsername = os.getenv('usgs_username')
usgsPassword = os.getenv('usgs_password')
targetTopic = os.getenv('target_topic')
targetBucket = os.getenv('target_bucket')


# Configure logging 
# Buffering: Sometimes, print statements may be buffered, meaning they are not immediately flushed to stdout. 
# This can cause delays in log visibility, especially when an instance is terminated. 
# Using logging ensures logs are handled and flushed properly.
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger('cloud-run-app')
app = Flask(__name__) 
app.logger.addHandler(logging.StreamHandler()) 
app.logger.setLevel(logging.INFO)


# Initialize Pub/Sub client
# Set up custom retry settings to disable retries 
customRetry = Retry(initial=1.0, maximum=1.0, multiplier=1.0, deadline=1.0)
publisher = pubsub_v1.PublisherClient(retry=customRetry) 
def publish(data):
    stringRep = json.dumps(data)
    base64Rep = stringRep.encode("ascii")
    future = publisher.publish(targetTopic, data=base64Rep)
    result = future.result()
    return result


@app.route("/")
def hello():
    return "Hello from downloader"

@app.route("/download", methods=["POST"])
def download():

    # step 1: get pubsub message
    envelope = request.get_json()
    if not envelope:
        return "Bad Request: no Pub/Sub message received", 400
    pubsub_message = envelope.get("message")
    if not pubsub_message:
        return "Bad Request: invalid Pub/Sub message format", 400
    data = base64.b64decode(pubsub_message.get("data", "")).decode("utf-8").strip()
    app.logger.info(f"Received message: {data}")

    # step 2: parse
    bbox = Bbox.fromString(data["bbox"])
    timeRange = TimeRange.fromStrings(data["startDate"], data["endDate"])

    # step 3: process
    outgoing = downloadData(logger, bbox, timeRange, targetBucket, usgsUsername, usgsPassword)

    # step 4: output
    publish(outgoing)
    return outgoing, 200