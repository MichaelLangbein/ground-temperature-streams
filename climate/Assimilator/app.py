import numpy as np
from flask import Flask, request
from google.cloud import pubsub_v1
from google.cloud import storage
from utils import Bbox, TimeRange
import base64
import logging
import os
import json
import shutil


# Getting environment variables
# targetTopic = os.getenv('target_topic')
# targetBucket = os.getenv('target_bucket')


# Configure logging
# Buffering: Sometimes, print statements may be buffered, meaning they are not immediately flushed to stdout.
# This can cause delays in log visibility, especially when an instance is terminated.
# Using logging ensures logs are handled and flushed properly.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('cloud-run-app')
app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler())
app.logger.setLevel(logging.INFO)


# Initialize bucket client
bucketClient = storage.Client()


def getFromBucket(bucketName, blobName, targetPath):
    bucket = bucketClient.get_bucket(bucketName)
    blob = bucket.blob(blobName)
    blob.download_to_filename(targetPath)


@app.route("/")
def hello():
    return "Hello from assimilator"


@app.route("/process", methods=["POST"])
def process():

    # step 1: get pubsub message
    envelope = request.get_json()
    if not envelope:
        return "Bad Request: no Pub/Sub message received", 400
    pubsub_message = envelope.get("message")
    if not pubsub_message:
        return "Bad Request: invalid Pub/Sub message format", 400
    data = base64.b64decode(pubsub_message.get(
        "data", "")).decode("utf-8").strip()
    app.logger.info(f"Received message: {data}")
    data = json.loads(data)

    # step 2: parse
    bucketName = data["bucketName"]
    blobName = data["blobName"]

    # step 3: process
    getFromBucket(bucketName, blobName)

    # step 4: output
    return outgoing, 200
