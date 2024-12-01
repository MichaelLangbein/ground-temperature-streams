# 1. Get data

## 1.1. Query index for relevant buckets

-   found on marketplace: https://console.cloud.google.com/marketplace/product/usgs-public-data/landast?project=climate-443420&cloudshell=true
-   Getting dataset: `bq ls --project_id=bigquery-public-data -n 10000 | grep cloud_storage_geo`
-   Getting tables: `bq ls bigquery-public-data:cloud_storage_geo_index`
-   Describing table: `bq show --format=prettyjson bigquery-public-data:cloud_storage_geo.landsat_index`
-   Querying data:
    ```sql
    select *
    from bigquery-public-data.cloud_storage_geo_index.landsat_index
    where date_acquired > date("2021-11-20")
    and west_lon > 11 and west_lon < 15
    and spacecraft_id = "LANDSAT_8";
    ```

## 1.2. Getting actual data

-   Listing files for one scene: `gsutils ls gs://gcp-public-data-landsat/LC08/01/190/032/LC08_L1TP_190032_20211217_20211223_01_T1`
-   Download one band: `gsutil cp gs://gcp-public-data-landsat/LC08/01/190/032/LC08_L1TP_190032_20211217_20211223_01_T1/LC08_L1TP_190032_20211217_20211223_01_T1_B10.TIF .`
