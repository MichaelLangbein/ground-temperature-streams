"""
- from USGS
- downloads full size images (not GeoTIFF)
- very recent (~ 12h old)
- requires authentication token
    - Token from: https://ers.cr.usgs.gov/password/appgenerate
"""

#%%

import datetime
from dataclasses import dataclass
import requests


@dataclass
class Bbox:
    lonMin: float
    lonMax: float
    latMin: float
    latMax: float
    
    def toList(self):
        return [self.lonMin, self.latMax, self.lonMax, self.latMax]
    
    def toString(self):
        return f"{self.toList()}"
    
    
@dataclass
class TimeRange:
    minTime: datetime.datetime
    maxTime: datetime.datetime
    
    

class M2M:
    """
    Docs: https://m2m.cr.usgs.gov/api/docs/json/
    """
    
    def __init__(self, userName, apiToken):
        self.userName = userName
        self.apiToken = apiToken
        self.apiUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
        self.session = requests.Session()
        self.authenticate()
        
    
    def authenticate(self):
        """
        Token from: https://ers.cr.usgs.gov/password/appgenerate
        Docs: https://m2m.cr.usgs.gov/api/docs/reference/login-token
        """
        
        if "X-Auth-Token" in self.session.headers:
            # already authenticated
            return
        
        loginUrl = f"{self.apiUrl}login-token"
        response = self.session.post(
            loginUrl,
            json={
                "username": self.userName, 
                "token": self.apiToken
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code} while trying to authenticate at `{loginUrl}`")
        
        content = response.json()
        apiKey = content["data"]
        self.session.headers["X-Auth-Token"] = apiKey

        print(f"Authenticating with {apiKey}")
        

    def datasetSearch(self, bbox: Bbox = None, timeRange: TimeRange = None, datasetName: str = None):
        """
        Lists datasets. Useful to get names of datasets for later scene search.
        """
        
        url = f"{self.apiUrl}dataset-search"
        payload = {}
        
        if bbox:
            payload["spatialFilter"] = {
                "filterType": "mbr",
                "lowerLeft":  { "latitude": bbox.latMin, "longitude": bbox.lonMin },
                "upperRight": { "latitude": bbox.latMax, "longitude": bbox.latMax }
            }
            
        if timeRange:
            payload["temporalFilter"] = {
                "start": timeRange.minTime.isoformat(),
                "end": timeRange.maxTime.isoformat()
            }
            
        if datasetName:
            payload["datasetName"] = datasetName
        
        response = self.session.post(
            url, 
            json=payload
        )
        
        datasets = response.json()
        datasetNames = [(el["datasetId"], el["datasetAlias"], el["datasetCategoryName"]) for el in datasets["data"]]
        
        return datasets, datasetNames
        
        
    def sceneSearch(
        self,
        datasetName: str = "landsat_ot_c2_l2",
        maxResults: int = None,
        timeRange: TimeRange = None,
        bbox: Bbox = None,
        maxCloudCover: int = None
    ):
        """
        Lists scenes inside a dataset. Useful to get IDs for download-requests
        https://m2m.cr.usgs.gov/api/docs/reference/#scene-search
        """
        
        sceneUrl = f"{self.apiUrl}scene-search"
        
        payload = {
            "datasetName": datasetName
        }
        
        if maxResults is not None:
            payload["maxResults"] = maxResults
            
        if timeRange or bbox or maxCloudCover:
            payload["sceneFilter"] = {}
            if timeRange:
                payload["sceneFilter"]["ingestFilter"] = {
                    "start": timeRange.minTime.isoformat(),
                    "end": timeRange.maxTime.isoformat()
                }
            if bbox:
                payload["sceneFilter"]["spatialFilter"] = {
                    "filterType": "mbr",
                    "lowerLeft":  { "latitude": bbox.latMin, "longitude": bbox.lonMin },
                    "upperRight": { "latitude": bbox.latMax, "longitude": bbox.latMax }
                }
            if maxCloudCover:
                payload["sceneFilter"]["cloudCoverFilter"] = {
                    "min": 0,
                    "max": maxCloudCover,
                    "includeUnknown": False
                }
                
        
        response = self.session.post(
            sceneUrl,
            json=payload
        )
        
        data = response.json()["data"]["results"]
        sceneIds = [r["entityId"] for r in data]
        
        return data, sceneIds
    
    
    def downloadOptions(self, sceneIds, datasetName: str = "landsat_ot_c2_l2"):
            
        url = f"{self.apiUrl}download-options"
        payload = {
            "datasetName" : datasetName, 
            "entityIds" : sceneIds
        }
                            
        response = self.session.post(url, payload)
        downloadOptions = response.json()
        
        return downloadOptions
        
        
    def quickDownload(
        self, 
        bbox: Bbox,
        timeRange: TimeRange,
        datasetName: str = "landsat_ot_c2_l2",
        maxCloudCover: int = None,
        maxResults: int = None
    ):
        data, sceneIds = self.sceneSearch(datasetName, maxResults, timeRange, bbox, maxCloudCover)
        # @TODO: get download options
        # @TODO: enqueue downloads
        # @TODO: fetch downloads
        
        
        
        
    
if __name__ == "__main__":

    # token, generated with https://ers.cr.usgs.gov/password/appgenerate
    token = "someToken"
    userName = "someName"
    bbox = Bbox(lonMin=11.2168, lonMax=11.3039, latMin=48.0582, latMax=48.1022)
    timeRange = TimeRange(minTime=datetime.date(2024, 11, 10), maxTime=datetime.date(2024, 11, 11))

    m2m = M2M(userName, token)
    datasets, datasetNames = m2m.datasetSearch(bbox, timeRange)
    data, sceneIds = m2m.sceneSearch(datasetName="landsat_ot_c2_l1", maxResults=10, timeRange=timeRange, bbox=bbox)
    downloadOptions = m2m.downloadOptions(datasetName="landsat_ot_c2_l1", sceneIds=sceneIds)
    downloadOptions