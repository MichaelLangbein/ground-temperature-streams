#! /bin/bash

docker compose down -v
docker container rm kafka_experiments-producer-1
docker image rm kafka_experiments-producer
docker container rm kafka_experiments-consumer-1
docker image rm kafka_experiments-consumer