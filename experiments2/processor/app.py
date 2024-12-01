from flask import Flask, request
from google.cloud import pubsub_v1
from google.api_core.retry import Retry
import base64
import logging
import os
import json


# Configure logging 
# Buffering: Sometimes, print statements may be buffered, meaning they are not immediately flushed to stdout. 
# This can cause delays in log visibility, especially when an instance is terminated. 
# Using logging ensures logs are handled and flushed properly.

logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger('cloud-run-app')
app = Flask(__name__) 
app.logger.addHandler(logging.StreamHandler()) 
app.logger.setLevel(logging.INFO)


# Getting environment variables
targetTopic = os.getenv('target_topic')


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


counter = 1

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/echo", methods=["POST"])
def echo():
    global counter

    envelope = request.get_json() 
    # app.logger.info(f"Received envelope: {json.dumps(envelope, indent=2)}") # Log the entire envelope
    if not envelope: 
        return "Bad Request: no Pub/Sub message received", 400 
    pubsub_message = envelope.get("message")
    if not pubsub_message:
        return "Bad Request: invalid Pub/Sub message format", 400 
    # Decode the Pub/Sub message data
    data = base64.b64decode(pubsub_message.get("data", "")).decode("utf-8").strip()
    app.logger.info(f"Received message: {data}")

    outgoing = {"currentCounter": counter}
    publish(outgoing)
    counter += 1
    app.logger.info(f"Published message: {outgoing}")

    return outgoing, 200