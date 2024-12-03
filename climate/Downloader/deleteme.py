# %%
from landsat import downloadLandsat8
from openmeteo import downloadOpenMeteo
from utils import Bbox, TimeRange
import numpy as np

# %% Parameters
username = "MichaelLangbein"
password = "RungeKutta5!"
bbox = Bbox(lonMin=10.74, latMin=47.85, lonMax=11.40,
            latMax=48.28, crs="epsg:4326")
timeRange = TimeRange.fromStrings(minTime="2021-01-10", maxTime="2021-01-12")
bands = ["B1", "B6", "QA_PIXEL"]


# %% Getting raw data from landsat

path, scenes = downloadLandsat8(username, password, bbox, timeRange, bands, 1)
print("successfully downloaded scenes: ", scenes, path)

# %% Getting point observations from open-meteo

for scene in scenes:
    bbox = scene["cutOffBbox"]
    bbox4326 = bbox.toCrs("epsg:4326")
    for i in range(10):
        lon = np.round(np.random.uniform(bbox4326.lonMin, bbox4326.lonMax), 4)
        lat = np.round(np.random.uniform(bbox4326.latMin, bbox4326.latMax), 4)
        path = downloadOpenMeteo(scene["display_id"], lon, lat, timeRange)

# %%
