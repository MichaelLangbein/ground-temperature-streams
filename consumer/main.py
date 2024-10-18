import json
from quixstreams import Application

app = Application(
    broker_address="localhost:9092",
    loglevel="DEBUG",
    consumer_group="weather_reader",
    # auto_offset_reset="latest" | "earliest"
)

with app.get_consumer() as consumer:
    consumer.subscribe(["weather_data_demo"])

    while True:
        msg = consumer.poll(1)
        if msg is None:
            print("Waiting ...")
        elif msg.error() is not None:
            raise Exception(msg.error())
        else:
            topic = msg.topic().decode("utf8")
            key = msg.key().decode("utf8")
            value = json.load(msg.value())
            offset = msg.offset()
            print((topic, key, value, offset))
            # consumer.store_offset(msg)
