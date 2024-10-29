FROM python:3.11

RUN apt-get update
RUN apt-get install python3-dev -y
RUN pip install kafka-python
RUN apt install dnsutils iputils-ping kcat -y


COPY ./main.py .

CMD python -u main.py 

