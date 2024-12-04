# %%
from download import download
from google.cloud import bigquery
import pandas as pd

bucketName = "data_bucket_climate123"
blobName = "data.zip"
extractedPath = "./data"

# %%
extractedPath = download(bucketName, blobName, extractedPath)

# %%
client = bigquery.Client()
dataset_ref = client.dataset("lst_dataset")
dataset = client.get_dataset(dataset_ref)
table = dataset.table("lst_table")


data = {
    'longitude': [122.0, 123.0],
    'latitude': [24.5, 25.0],
    'h3index': ['85283473fffffff', '85283477fffffff'],
    'date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')],
    'landSurfaceTemperature': [45.0, 47.0]
}

df = pd.DataFrame(data)

schema = [
    bigquery.SchemaField("longitude", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("latitude", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("h3index", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("landSurfaceTemperature", "FLOAT", mode="NULLABLE"),
]

# appends data
# depends on pyarrow
job = client.load_table_from_dataframe(
    dataframe=df,
    destination=table,
    job_config=bigquery.LoadJobConfig(schema=schema)
)
result = job.result()
result

# %%
