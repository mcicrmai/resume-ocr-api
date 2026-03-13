from flask import Flask, request, jsonify
import pytesseract
from PIL import Image

app = Flask(__name__)

@app.route('/ocr', methods=['POST'])
def ocr():
    # Expecting a file upload with key "File"
    if 'File' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['File']
    img = Image.open(file.stream)
    text = pytesseract.image_to_string(img)

    return jsonify({
        "raw_text": text
    })

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)