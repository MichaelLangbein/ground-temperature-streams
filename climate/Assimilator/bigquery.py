# %%
from dataclasses import dataclass
from typing import List
from google.cloud import bigquery
import pandas as pd


@dataclass
class Data:
    longitude: List[float]
    latitude: List[float]
    h3index: List[str]
    date: List[pd.Timestamp]
    landSurfaceTemperature: List[float]


schema = [
    bigquery.SchemaField("longitude", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("latitude", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("h3index", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("landSurfaceTemperature",
                         "FLOAT", mode="NULLABLE"),
]


def uploadCsv(filePath: str, datasetName="lst_dataset", tableName="lst_table"):
    client = bigquery.Client()
    dataset_ref = client.dataset(datasetName)
    dataset = client.get_dataset(dataset_ref)
    table = dataset.table(tableName)

    # appends data
    with open(filePath, "rb") as fh:
        job = client.load_table_from_file(
            fh, destination=table, job_config=bigquery.LoadJobConfig(schema=schema))
        result = job.result()
        return result


def uploadData(data: Data, datasetName="lst_dataset", tableName="lst_table"):
    df = pd.DataFrame({
        'longitude': pd.Series(dtype='float'),
        'latitude': pd.Series(dtype='float'),
        'h3index': pd.Series(dtype='string'),
        'date': pd.Series(dtype='datetime64[ns]'),
        'landSurfaceTemperature': pd.Series(dtype='float')
    })
    df['longitude'] = data.longitude
    df['latitude'] = data.latitude
    df['h3index'] = data.h3index
    df['date'] = data.date
    df['landSurfaceTemperature'] = data.landSurfaceTemperature
    return uploadData(df, datasetName, tableName)


def uploadDataFrame(df: pd.DataFrame, datasetName="lst_dataset", tableName="lst_table"):
    client = bigquery.Client()
    dataset_ref = client.dataset(datasetName)
    dataset = client.get_dataset(dataset_ref)
    table = dataset.table(tableName)

    # appends data
    # depends on pyarrow
    job = client.load_table_from_dataframe(
        dataframe=df,
        destination=table,
        job_config=bigquery.LoadJobConfig(schema=schema)
    )
    result = job.result()
    return result

# %%
