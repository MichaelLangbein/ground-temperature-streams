# %% imports
from utils import Bbox, TimeRange
from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer
import tarfile
import rasterio
from rasterio.windows import from_bounds
import os


# %% final code

def cutGeotiff(inputTiffPath: str, outputTiffPath: str, bbox: Bbox):
    # Open the input GeoTIFF file
    with rasterio.open(inputTiffPath) as inputFile:
        bboxTransformed = bbox.toCrs(inputFile.crs)

        # Get the bounds of the raster
        left, bottom, right, top = inputFile.bounds
        sourceBbox = Bbox(lonMin=left, latMin=bottom,
                          lonMax=right, latMax=top, crs=inputFile.crs)
        if not sourceBbox.intersects(bboxTransformed):
            raise ValueError(
                "The source bbox does not intersect the target bbox", sourceBbox, bboxTransformed)
        cutOffBbox = bboxTransformed.getOverlap(sourceBbox)

        # Define the window using bounding box coordinates
        window = from_bounds(
            left=cutOffBbox.lonMin, bottom=cutOffBbox.latMin,
            right=cutOffBbox.lonMax, top=cutOffBbox.latMax,
            transform=inputFile.transform
        )
        # Read the data from the defined window
        data = inputFile.read(window=window)
        # Update the metadata with the new window's transform
        transform = inputFile.window_transform(window)
        metadata = inputFile.meta.copy()
        metadata.update(
            {'height': window.height, 'width': window.width, 'transform': transform})
        # Write the cut-out data to a new GeoTIFF file
        with rasterio.open(outputTiffPath, 'w+', **metadata) as dst:
            dst.write(data)


def downloadOne(username: str, password: str, bbox: Bbox, timeRange: TimeRange, bands: list[str]):
    allowedBands = [
        "B1", "B2", "B3", "B4", "B5", "B6", "B8", "B9", "B10", "B11",
        "QA_PIXEL", "QA_RADSAT", "SAA", "SZA", "VAA", "VZA"
    ]
    for band in bands:
        if band not in allowedBands:
            raise Exception(f"Band {band} is not allowed.")
    centerPoint = bbox.center()
    downloadTarInto = './tmpData'
    extractTarInto = './tmpData/extracted/'
    saveCutoutTo = "./tmpData/cutout/"
    os.makedirs(extractTarInto, exist_ok=True)
    os.makedirs(saveCutoutTo, exist_ok=True)

    api = API(username, password)
    scenes = api.search(
        dataset='landsat_ot_c2_l1',
        latitude=centerPoint.lat,
        longitude=centerPoint.lon,
        start_date=timeRange.minTime.strftime('%Y-%m-%d'),
        end_date=timeRange.maxTime.strftime('%Y-%m-%d'),
        max_cloud_cover=10
    )
    print(f"Got {len(scenes)} scenes: ", scenes)
    api.logout()

    ee = EarthExplorer(username, password)
    for scene in scenes:
        # check if already exists:
        if os.path.exists(f"{downloadTarInto}/{scene['display_id']}.tar"):
            downloadedTarPath = f"{downloadTarInto}/{scene['display_id']}.tar"
            break
        sceneBbox = Bbox(
            lonMin=scene["corner_lower_left_longitude"],
            lonMax=scene["corner_upper_right_longitude"],
            latMin=scene["corner_lower_left_latitude"],
            latMax=scene["corner_upper_right_latitude"],
            crs="WGS84"
        )
        downloadedTarPath = ee.download(
            scene["entity_id"], output_dir=downloadTarInto)
        print("Got file: ", downloadedTarPath)
        break
    ee.logout()

    if not downloadedTarPath:
        raise Exception("No file downloaded")

    sceneId = os.path.basename(downloadedTarPath).split(".")[0]

    with tarfile.TarFile(downloadedTarPath, 'r') as t:
        t.extractall(extractTarInto)

    for band in bands:
        sourceTiffPath = f"{extractTarInto}/{sceneId}_{band}.TIF"
        targetTiffPath = f"{saveCutoutTo}/{sceneId}_{band}.TIF"
        cutGeotiff(sourceTiffPath, targetTiffPath, bbox)
        print("Saved Tiff: ", targetTiffPath)

    return saveCutoutTo, scene


# %% Parameters
# token = "eWq_u911K_9NT5CY2YeIFNs23iG@CpH_Jz9slMvzu5yt05uyXc5N8122NregULu_"
username = "MichaelLangbein"
password = "RungeKutta5!"
bbox = Bbox(lonMin=10.74, latMin=47.85, lonMax=11.40,
            latMax=48.28, crs="epsg:4326")
centerPoint = bbox.center()
timeRange = TimeRange.fromStrings(minTime="2020-05-01", maxTime="2021-01-25")
bands = ["B1", "B6", "QA_PIXEL", ]


path, scene = downloadOne(username, password, bbox, timeRange, bands)
print("successfully downloaded scene: ", scene, path)

# %% Get scenes


api = API(username, password)
scenes = api.search(
    dataset='landsat_ot_c2_l1',
    latitude=centerPoint.lat,
    longitude=centerPoint.lon,
    start_date=timeRange.minTime.strftime('%Y-%m-%d'),
    end_date=timeRange.maxTime.strftime('%Y-%m-%d'),
    max_cloud_cover=10
)
api.logout()

print(scenes)


# %% Download scenes

ee = EarthExplorer(username, password)
for scene in scenes:
    # Downloads can fail. Try out scenes until one is successfully downloaded.
    localFilePath = ee.download(scene["entity_id"], output_dir='./tmpData')
    if localFilePath:
        break
    # cutOut(localFilePath, bbox, targetPath)
ee.logout()

# %% extract scene


targetDir = "./tmpData/extracted"
with tarfile.TarFile(localFilePath, 'r') as t:
    t.extractall(targetDir)

# %% cut out

unzipTargetDir = "./tmpData/extracted"
sceneId = "LC08_L1TP_194027_20210111_20210307_02_T1"
bands = [
    "B1", "B6", "QA_PIXEL"
]
cutoutDir = "./tmpData/cutout"
os.makedirs(cutoutDir, exist_ok=True)

for band in bands:
    bandFilePath = f"{unzipTargetDir}/{sceneId}_{band}.TIF"
    inputTiffPath = bandFilePath
    outputTiffPath = f"{cutoutDir}/{sceneId}_{band}.TIF"
    # cutGeotiff(inputTiffPath, outputTiffPath, bbox)

    with rasterio.open(inputTiffPath) as src:
        bboxTransformed = bbox.toCrs(src.crs)

        # Get the bounds of the raster
        left, bottom, right, top = src.bounds
        sourceBbox = Bbox(lonMin=left, latMin=bottom,
                          lonMax=right, latMax=top, crs=src.crs)
        if not sourceBbox.intersects(bboxTransformed):
            raise ValueError(
                "The source bbox does not intersect the target bbox", sourceBbox, bboxTransformed)
        cutOffBbox = bboxTransformed.getOverlap(sourceBbox)

        # Define the window using bounding box coordinates
        window = from_bounds(
            left=cutOffBbox.lonMin, bottom=cutOffBbox.latMin,
            right=cutOffBbox.lonMax, top=cutOffBbox.latMax,
            transform=src.transform
        )
        # Read the data from the defined window
        data = src.read(window=window)
        # Update the metadata with the new window's transform
        transform = src.window_transform(window)
        metadata = src.meta.copy()
        metadata.update(
            {'height': window.height, 'width': window.width, 'transform': transform})
        # Write the cut-out data to a new GeoTIFF file
        with rasterio.open(outputTiffPath, 'w', **metadata) as dst:
            dst.write(data)


# %%
