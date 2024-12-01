from flask import Flask, request
import json
import base64
import logging


# Configure logging 
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger('cloud-run-app') 
app = Flask(__name__) 
app.logger.addHandler(logging.StreamHandler()) 
app.logger.setLevel(logging.INFO)

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/echo", methods=["POST"])
def echo():
    envelope = request.get_json() 
    app.logger.info(f"Received envelope: {json.dumps(envelope, indent=2)}") # Log the entire envelope
    if not envelope: 
        return "Bad Request: no Pub/Sub message received", 400 
    pubsub_message = envelope.get("message") 
    if not pubsub_message: 
        return "Bad Request: invalid Pub/Sub message format", 400 
    # Decode the Pub/Sub message data 
    data = base64.b64decode(pubsub_message.get("data", "")).decode("utf-8").strip() 
    app.logger.info(f"Received message: {data}")
    return data, 200