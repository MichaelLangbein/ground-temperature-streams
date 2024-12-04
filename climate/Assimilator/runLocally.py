# %%
from download import download
from bigquery import uploadData, Data
import pandas as pd

bucketName = "data_bucket_climate123"
blobName = "data.zip"
extractedPath = "./data"

# %%
extractedPath = download(bucketName, blobName, extractedPath)

# %%
data = Data(
    longitude=[10.0, 11.0],
    latitude=[40.0, 41.0],
    h3index=["fdsafsd", "fdsafds"],
    date=[pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-02")],
    landSurfaceTemperature=[12.1, 14.2]
)
result = uploadData(data, datasetName="lst_dataset", tableName="lst_table")

# %%
