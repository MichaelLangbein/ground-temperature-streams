from flask import Flask
from flask import request
import json
import base64


app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/echo", methods=["POST"])
def echo():
    envelope = request.get_json() 
    print(f"Received envelope: {json.dumps(envelope, indent=2)}") # Log the entire envelope
    if not envelope: 
        return "Bad Request: no Pub/Sub message received", 400 
    pubsub_message = envelope.get("message") 
    if not pubsub_message: 
        return "Bad Request: invalid Pub/Sub message format", 400 
    # Decode the Pub/Sub message data 
    data = base64.b64decode(pubsub_message.get("data", "")).decode("utf-8").strip() 
    print(f"Received message: {data}")
    return data, 200