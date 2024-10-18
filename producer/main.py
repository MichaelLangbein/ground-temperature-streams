import requests
import time
import json
from quixstreams import Application
from argparse import ArgumentParser
import logging



def fetchData(lon=51.5, lat=-0.11, kind="temperature_2m"):
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lon,
            "longitude": lat,
            "current": kind
        }
    )
    data = response.json()
    return data


def produce(lon=51.5, lat=-0.11, kind="temperature_2m", sleepTime=3, broker="http://broker:9092"):

    app = Application(
        broker_address=broker,
        loglevel="DEBUG"
    )

    with app.get_producer() as producer:

        while True:
            data = fetchData(lon, lat, kind)

            producer.produce(
                topic="weather_data_demo",
                key="London",
                value=json.dumps(data)
            )
            time.sleep(sleepTime)



if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("--lon", default=12.0, type=float)
    parser.add_argument("--lat", default=45.0, type=float)
    parser.add_argument("--kind", default="temperature_2m", type=str)
    parser.add_argument("--sleep", default=3, type=int)
    parser.add_argument("--broker", default="http://broker:9092", type=str)
    args = parser.parse_args()

    logging.info(f"Running producer with arguments: lon: {args.lon}, lat: {args.lat}, kind: {args.kind}, sleep: {args.sleep}, broker: {args.broker}")

    produce(args.lon, args.lat, args.kind, args.sleep, args.broker)


