# from retry_requests import retry
# import requests_cache
import pandas as pd
import openmeteo_requests
import numpy as np


# Setup the Open-Meteo API client with cache and retry on error
# https://open-meteo.com/en/docs/historical-weather-api

# cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
# retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
# openmeteo = openmeteo_requests.Client(session=retry_session)
openmeteo = openmeteo_requests.Client()


def downloadOpenMeteo(saveCsvsTo: str, displayId: str, lon: int, lat: int, timeRange):

    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": timeRange.minTime.strftime("%Y-%m-%d"),
        "end_date": timeRange.maxTime.strftime("%Y-%m-%d"),
        "hourly": "temperature_2m"
    }
    responses = openmeteo.weather_api(url, params=params)

    # should only be one
    for response in responses:

        hourly = response.Hourly()
        hourlyTemperature2m = hourly.Variables(0).ValuesAsNumpy()

        hourlyData = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            ),
            "temperature_2m": hourlyTemperature2m
        }

        hourlyDataFrame = pd.DataFrame(data=hourlyData)

        targetFilePath = f"{saveCsvsTo}/{displayId}_lat{lat}_lon{lon}.csv"
        hourlyDataFrame.to_csv(targetFilePath, index=False)

        return targetFilePath
