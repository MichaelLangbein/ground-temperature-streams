#%%
from google.cloud import storage


def entryPoint(event, context):
    print("Event: ", event)

    storageClient = storage.Client()
    bucketIterator = storageClient.list_buckets(
        prefix='ecmwf-open-data'
    )
    buckets = list(bucketIterator)

    print(f"Results: {len(buckets)}")

