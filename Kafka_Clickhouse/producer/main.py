from kafka import KafkaProducer
from datetime import datetime
import json
import time

print("connecting to kafka:9092 ...")


producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

body = {
    'author': 'michael', 
    'content': 'some body', 
    'created_at': datetime.now().isoformat()
}

while True:
    body["created_at"] = datetime.now().isoformat()
    producer.send('posts',  body)
    time.sleep(3)