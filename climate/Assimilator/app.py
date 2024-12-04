import pandas as pd
from flask import Flask, request
from download import download
from bigquery import uploadData, Data
import base64
import logging
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

    # step 3: download
    downloadInto = "./data"
    downloadedPath = download(bucketName, blobName, downloadInto)

    # step 4: process
    # @TODO

    # step 5: upload
    data = Data(
        longitude=[10.0, 11.0],
        latitude=[40.0, 41.0],
        h3index=["fdsafsd", "fdsafds"],
        date=[pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-02")],
        landSurfaceTemperature=[12.1, 14.2]
    )
    result = uploadData(data, datasetName="lst_dataset",
                        tableName="lst_table")

    # step 4: output
    return {"result": "success"}, 200
