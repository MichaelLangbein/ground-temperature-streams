from utils import Bbox, TimeRange
from landsat import downloadLandsat8
from openmeteo import downloadOpenMeteo
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


def downloadData(
    logger,
    bbox: Bbox, timeRange: TimeRange,
    usgsUsername: str, usgsPassword: str
):

    bands = ["B1", "B6", "QA_PIXEL"]
    path = os.path.abspath("./zipData")

    landsatPath, scenes = downloadLandsat8(
        path, usgsUsername, usgsPassword, bbox, timeRange, bands, 1)
    logger.info(f"successfully downloaded scenes: {len(scenes)} into {path}")

    for scene in scenes:
        bbox = scene["cutOffBbox"]
        bbox4326 = bbox.toCrs("epsg:4326")
        for i in range(10):
            lon = np.round(np.random.uniform(
                bbox4326.lonMin, bbox4326.lonMax), 4)
            lat = np.round(np.random.uniform(
                bbox4326.latMin, bbox4326.latMax), 4)
            csvPath = downloadOpenMeteo(
                path, scene["display_id"], lon, lat, timeRange)
    logger.info(f"successfully downloaded open-meteo data into {path}")

    logger.warn("now zipping ...")
    zipFileName = shutil.make_archive(
        base_name="data", format='zip', root_dir=path)
    logger.warn(f"""successfully zipped into {zipFileName} at {
                os.path.abspath(zipFileName)}""")

    return os.path.abspath(zipFileName)


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
publisher = pubsub_v1.PublisherClient()


def publish(topicName: str, data):
    stringRep = json.dumps(data)
    base64Rep = stringRep.encode("ascii")
    future = publisher.publish(topicName, data=base64Rep)
    result = future.result()
    return result


# Initialize bucket client
bucketClient = storage.Client()


def writeToBucket(bucketName, blobName, filePath):
    bucket = bucketClient.get_bucket(bucketName)
    blob = bucket.blob(blobName)
    blob.upload_from_filename(filePath)


# Subscriptions are a bit hyperactive:
# they will try to resend a message if an error occurs.
# The earthexplorer api, however, doesn't like
# parallel requests.
lock = False


@app.route("/")
def hello():
    return "Hello from downloader"


@app.route("/download", methods=["POST"])
def download():
    global lock
    if lock == True:
        return "busy", 503
    lock = True

    # step 1: get pubsub message
    envelope = request.get_json()
    if not envelope:
        lock = False
        return "Bad Request: no Pub/Sub message received", 400
    pubsub_message = envelope.get("message")
    if not pubsub_message:
        lock = False
        return "Bad Request: invalid Pub/Sub message format", 400
    data = base64.b64decode(pubsub_message.get(
        "data", "")).decode("utf-8").strip()
    app.logger.info(f"Received message: {data}")
    data = json.loads(data)

    # step 2: parse
    lonMin = float(data["lonMin"])
    lonMax = float(data["lonMax"])
    latMin = float(data["latMin"])
    latMax = float(data["latMax"])
    bbox = Bbox(lonMin, latMin, lonMax, latMax)
    timeRange = TimeRange.fromStrings(data["startDate"], data["endDate"])

    # step 3: process
    zipFilePath = downloadData(logger, bbox, timeRange,
                               usgsUsername, usgsPassword)
    blobName = os.path.basename(zipFilePath)
    writeToBucket(targetBucket, blobName, zipFilePath)

    # step 4: output
    outgoing = {
        "bucketName": targetBucket,
        "blobName": blobName
    }
    publish(targetTopic, outgoing)
    lock = False
    return outgoing, 200
