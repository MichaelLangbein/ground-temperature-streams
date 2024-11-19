import rasterio as rio
from pyproj.transformer import Transformer


def downloadGeoTiff(href, bbox):
    with rio.open(href) as fh:
        coordTransformer = Transformer.from_crs('EPSG:4326', fh.crs)
        coordUpperLeft = coordTransformer.transform(bbox[3], bbox[0])
        coordLowerRight = coordTransformer.transform(bbox[1], bbox[2])
        pixelUpperLeft = fh.index( coordUpperLeft[0],  coordUpperLeft[1] )
        pixelLowerRight = fh.index( coordLowerRight[0],  coordLowerRight[1] )
        # make http range request only for bytes in window
        window = rio.windows.Window.from_slices(
            ( pixelUpperLeft[0],  pixelLowerRight[0] ),
            ( pixelUpperLeft[1],  pixelLowerRight[1] )
        )
        subset = fh.read(1, window=window)
        return subset