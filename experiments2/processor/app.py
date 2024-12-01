from flask import Flask
from flask import request
import base64


app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/echo", methods=["POST"])
def echo():
    message = request.get_json()
    body = base64.b64decode(message["message"]["data"]).decode("utf-8").strip()
    print(message)
    return body