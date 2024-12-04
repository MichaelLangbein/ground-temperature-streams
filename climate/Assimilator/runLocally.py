from download import download

bucketName = "data_bucket_climate123"
blobName = "data.zip"
extractedPath = "./data"

extractedPath = download(bucketName, blobName, extractedPath)
