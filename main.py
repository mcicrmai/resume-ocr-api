from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Resume OCR API is running!"