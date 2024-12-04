# %%
from utils import Bbox, TimeRange
import shutil
import numpy as np
from landsat import downloadLandsat8
from openmeteo import downloadOpenMeteo


# %%
def downloadData(
    bbox: Bbox, timeRange: TimeRange,
    usgsUsername: str, usgsPassword: str
):

    bands = ["B1", "B6", "QA_PIXEL"]
    path = "./zipData"

    landsatPath, scenes = downloadLandsat8(
        path, usgsUsername, usgsPassword, bbox, timeRange, bands, 1)

    for scene in scenes:
        bbox = scene["cutOffBbox"]
        bbox4326 = bbox.toCrs("epsg:4326")
        for i in range(10):
            lon = np.round(np.random.uniform(
                bbox4326.lonMin, bbox4326.lonMax), 4)
            lat = np.round(np.random.uniform(
                bbox4326.latMin, bbox4326.latMax), 4)
            csvPath = downloadOpenMeteo(
                path, scene["display_id"], lon, lat, timeRange)

    zipFileName = shutil.make_archive(
        base_name="data", format='zip', root_dir=path)

    return f"./{zipFileName}"


# %%
with open("../Infrastructure/terraform.tfvars", "r") as f:
    for line in f:
        if line.startswith("usgs_username"):
            usgsUsername = line.split("=")[1].strip().replace('"', '')
        if line.startswith("usgs_password"):
            usgsPassword = line.split("=")[1].strip().replace('"', '')


bbox = Bbox(
    lonMin=12,
    latMin=45,
    lonMax=12.5,
    latMax=45.5,
    crs="epsg:4326")

timeRange = TimeRange.fromStrings(
    minTime="2021-01-01",
    maxTime="2021-01-17")

# %%
zipFilePath = downloadData(bbox, timeRange,
                           usgsUsername, usgsPassword)

print(zipFilePath)
# %%
