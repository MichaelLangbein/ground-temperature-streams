FROM python:3.12.7-bookworm

RUN apt-get update
RUN apt-get install python3-dev -y
RUN pip install requests quixstreams

COPY ./main.py .

ENV lon 12
ENV lat 45
ENV kind "temperature_2m"
ENV sleep 3
ENV broker "http://broker:9092"

SHELL [ "/bin/bash", "-c" ]

CMD python main.py --lon $lon --lat $lat --kind $kind --sleep $sleep --broker $broker