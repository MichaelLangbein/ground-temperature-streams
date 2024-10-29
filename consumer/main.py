from kafka import KafkaConsumer
import json
import time


# time.sleep(30)
print("connecting to kafka:9092 ...")

consumer = KafkaConsumer(
    'posts',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# note that this for loop will block forever to wait for the next message
for message in consumer:
    print(message.value)