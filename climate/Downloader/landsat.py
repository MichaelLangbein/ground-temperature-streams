from utils import Bbox, TimeRange
from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer
import tarfile
import rasterio
from rasterio.windows import from_bounds
import os


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

    return outputTiffPath, cutOffBbox


def downloadLandsat8(saveCutoutTo: str, username: str, password: str, bbox: Bbox, timeRange: TimeRange, bands: list[str], maxNr: int = 1):
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
    downloadedScenes = []
    for i, scene in enumerate(scenes):
        if i >= maxNr:
            break

        # check if already exists:
        if os.path.exists(f"{downloadTarInto}/{scene['display_id']}.tar"):
            downloadedTarPath = f"{downloadTarInto}/{scene['display_id']}.tar"

        # else download
        else:
            downloadedTarPath = ee.download(
                scene["entity_id"], output_dir=downloadTarInto)
            print("Got file: ", downloadedTarPath)

        sceneId = os.path.basename(downloadedTarPath).split(".")[0]

        # extract
        with tarfile.TarFile(downloadedTarPath, 'r') as t:
            t.extractall(extractTarInto)

        # cut
        for band in bands:
            sourceTiffPath = f"{extractTarInto}/{sceneId}_{band}.TIF"
            targetTiffPath = f"{saveCutoutTo}/{sceneId}_{band}.TIF"
            outputTiffPath, cutOffBbox = cutGeotiff(
                sourceTiffPath, targetTiffPath, bbox)
            scene["cutOffBbox"] = cutOffBbox
            print("Saved Tiff: ", outputTiffPath)

        downloadedScenes.append(scene)

    ee.logout()

    return saveCutoutTo, downloadedScenes
