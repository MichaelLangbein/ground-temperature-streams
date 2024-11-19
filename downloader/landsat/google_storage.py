"""
- from google
    - https://cloud.google.com/storage/docs/public-datasets/landsat
- GeoTIFFS
    - But not COG's, so not possible to download part of file?
- historical only (2013 - 2021)
- Level 1
- when running locally, requires gcloud to be installed, and auth mechanism must have been configured
    - install gcloud cli
    - enable authentication for gcloud cli (gcloud auth login)
    - create a project
    - enable billing for that project
"""


"""
The images are organized in the Worldwide Reference System (WRS-2) grid, which is a global grid dividing the world into 251 orbital paths and 248 rows. Different Landsat satellites have used sensors with slightly different characteristics, so Cloud Storage organizes the data by sensor in the following effective directory structure:

/SENSOR_ID/01/PATH/ROW/SCENE_ID/

The components of this path are:

    SENSOR_ID: An identifier for the particular satellite and camera sensor.
    01: An indicator that the data is part of Landsat Collection 1.
    PATH: The WRS path number.
    ROW: The WRS row number.
    SCENE_ID: The unique scene ID.

As an example, one Landsat 8 scene over California can be found here:

gs://gcp-public-data-landsat/LC08/01/044/034/LC08_L1GT_044034_20130330_20170310_01_T2/

To help locate data of interest, an index CSV file of the Landsat data is available. This CSV file lists basic properties of the available images, including their acquisition dates and their spatial extent as minimum and maximum latitudes and longitudes. The file is found in the Landsat Cloud Storage bucket:

gs://gcp-public-data-landsat/index.csv.gz


"""

#%% 0. utils
import os
from utils import Bbox, TimeRange


localDir = os.path.dirname(os.path.abspath(__file__))
targetBbox = Bbox(
    lonMin=11.2168,
    lonMax=11.3039,
    latMin=48.0582,
    latMax=48.1022
)
targetTimeRange = TimeRange(
    minTime=datetime.date(2019, 11, 1), 
    maxTime=datetime.date(2019, 11, 11)
)




#%% 1. getting index csv

import gzip
from google.cloud import storage




if not os.path.exists(localDir + "/index.csv"):

    client = storage.Client()
    bucket = client.bucket("gcp-public-data-landsat")
    blob = bucket.blob("index.csv.gz")
    blob.download_to_filename("index.csv.gz")


    with gzip.open("index.csv.gz", "rb") as gzipped:
        with open("index.csv", "wb") as plaintext:
            plaintext.write(gzipped.read())



#%% 2. reading relevant data

import csv
import datetime

selectedScenes = []

with open(f"{localDir}/index.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:

        bbox = Bbox(
            lonMin=float(row["WEST_LON"]),
            lonMax=float(row["EAST_LON"]),
            latMin=float(row["SOUTH_LAT"]),
            latMax=float(row["NORTH_LAT"]),
        )
        acquired = datetime.date.fromisoformat(row["DATE_ACQUIRED"])

        if targetTimeRange.contains(acquired):
            if bbox.intersects(targetBbox):
                selectedScenes.append(row)


with open(f"{localDir}/selectedScenes.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=selectedScenes[0].keys())
    writer.writeheader()
    writer.writerows(selectedScenes)


# %%
import rasterio as rio

selectedScenes = []

with open(f"{localDir}/selectedScenes.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        datum = {
            "acquired": datetime.date.fromisoformat(row["DATE_ACQUIRED"]),
            # "sensingTime": datetime.datetime.fromisoformat(row["SENSING_TIME"]),
            "bbox": Bbox(
                lonMin=float(row["WEST_LON"]),
                lonMax=float(row["EAST_LON"]),
                latMin=float(row["SOUTH_LAT"]),
                latMax=float(row["NORTH_LAT"]),
            ),
            "cloudCover": float(row["CLOUD_COVER"]),
            "sceneId": row["SCENE_ID"],
            "productId": row["PRODUCT_ID"],
            "sensorId": row["SENSOR_ID"],
            "spacecraftId": row["SPACECRAFT_ID"],
            "collectionNumber": row["COLLECTION_NUMBER"],
            "collectionCategory": row["COLLECTION_CATEGORY"],
            "dataType": row["DATA_TYPE"],
            "wrsPath": row["WRS_PATH"],
            "wrsRow": row["WRS_ROW"],
            "baseUrl": row["BASE_URL"],
        }
        selectedScenes.append(datum)



client = storage.Client()
bucket = client.bucket("gcp-public-data-landsat")

for scene in selectedScenes:
    blobUrl = scene["baseUrl"].replace("gs://gcp-public-data-landsat", "")
    blob = bucket.blob(blobUrl)
    blob.download_to_filename(f"{localDir}/{scene['sceneId']}.zip")

