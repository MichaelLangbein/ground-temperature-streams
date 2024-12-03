FROM python:3.11
# must be <= 3.11 for landsatxplore

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Per default, cloud run sends traffic to port 8080 (using an env variable)
# If deployment takes long, it might be because gcp is trying for minutes to 
# access port 8080 even though you haven't made it available.
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=8080"]
