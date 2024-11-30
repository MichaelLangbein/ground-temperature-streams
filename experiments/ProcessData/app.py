from flask import Flask
from flask import request


app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/echo", methods=["POST"])
def echo():
    print(request.json)
    return request.json