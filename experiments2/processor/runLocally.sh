#! /bin/bash

docker image build -t processor .
docker container run --rm -p 8080:8080 processor