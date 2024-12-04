import os
import zipfile
from google.cloud import storage


bucketClient = storage.Client()


def getFromBucket(bucketName, blobName, targetPath):
    bucket = bucketClient.get_bucket(bucketName)
    blob = bucket.blob(blobName)
    blob.download_to_filename(targetPath)


bucketName = "data_bucket_climate123"
blobName = "data.zip"
zipFilePath = "./data.zip"
extractedPath = "./data"

if not os.path.exists(zipFilePath):
    getFromBucket(bucketName, blobName, zipFilePath)

with zipfile.ZipFile(zipFilePath, "r") as zf:
    zf.extractall(extractedPath)
