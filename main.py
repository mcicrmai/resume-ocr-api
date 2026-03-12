from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import os

app = Flask(__name__)

# If you ever run locally on Windows, set Tesseract path
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

@app.route("/extract", methods=["POST"])
def extract_text():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    img = Image.open(file.stream)
    text = pytesseract.image_to_string(img)

    # Simple parser for your example fields
    parsed_data = {}
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("WP No."):
            parsed_data["wp_no"] = line.split(":")[1].strip()
        elif line.startswith("Name of Worker"):
            parsed_data["name"] = line.split(":")[1].strip()
        elif line.startswith("DOB of Worker"):
            parsed_data["dob"] = line.split(":")[1].strip()
        elif line.startswith("Sex"):
            parsed_data["sex"] = line.split(":")[1].strip()
        elif line.startswith("Worker's FIN"):
            parsed_data["fin"] = line.split(":")[1].strip()
        elif line.startswith("Passport No."):
            parsed_data["passport"] = line.split(":")[1].strip()
        elif line.startswith("Nationality/Citizenship"):
            parsed_data["nationality"] = line.split(":")[1].strip()

    return jsonify({
        "parsed_data": parsed_data,
        "raw_text": text
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)