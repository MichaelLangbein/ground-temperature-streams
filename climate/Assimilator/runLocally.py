import os
import zipfile
from google.cloud import storage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('cloud-run-app')


def download(bucketName: str, blobName: str, extractedPath: str):

    bucketClient = storage.Client()

    extractedPath = os.path.abspath(extractedPath)
    zipFilePath = os.path.abspath("./data.zip")

    if not os.path.exists(zipFilePath):
        logger.info(f"""Downloading from bucket ({
                    bucketName}/{blobName}) into {extractedPath}...""")
        bucket = bucketClient.get_bucket(bucketName)
        blob = bucket.blob(blobName)
        blob.download_to_filename(zipFilePath)
        logger.info("... download successful.")

    if not os.path.exists(extractedPath) or len(os.listdir(extractedPath)) == 0:
        logger.info("extracting ...")
        with zipfile.ZipFile(zipFilePath, "r") as zf:
            zf.extractall(extractedPath)
        os.remove(zipFilePath)
        logger.info("... extracting successful.")


bucketName = "data_bucket_climate123"
blobName = "data.zip"
extractedPath = "./data"

download(bucketName, blobName, extractedPath)
