from google.cloud import storage


def scanForNewData(event, context):
    print(f'Heartbeat received: {context.event_id}')
    
    storageClient = storage.Client()
    buckets = list(storageClient.list_buckets(prefix='ecmwf-open-data'))
    
    print(f"List of buckets (count: {len(bucket)}):") 
    for bucket in buckets: 
        print(bucket.name) 
    