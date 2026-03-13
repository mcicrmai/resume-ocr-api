from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import os
import re

app = Flask(__name__)

# Windows only: set Tesseract path
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# On Render (Linux), Tesseract will be installed via apt-get and available in PATH

def extract_worker_details(text):
    details = {}
    patterns = {
        "WP_No": r"WP\s*No\.?\s*:?\s*([A-Z0-9\s]+)$",
        "Name": r"Name\s*(?:of\s*Worker)?[:\s]*([A-Za-z\s]+)(?=\n|$)",
        "Date_of_Birth": r"(?:DOB|Date\s*of\s*Birth)\s*(?:of\s*Worker)?[:\s]*([0-9/]+)$",
        "Sex": r"Sex[:\s]*([A-Za-z]+)$",
        "FIN": r"(?:FIN|Worker's\s*FIN)[:\s]*([A-Z0-9]+)$",
        "Passport_No": r"Passport\s*No\.?\s*:?\s*([A-Z0-9\s]+)$",
        "Nationality": r"(?:Nationality|Citizenship)[^:]*[:\s]*([A-Za-z]+)$"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            if key in ["WP_No", "FIN", "Passport_No"]:
                value = value.replace(" ", "")
            details[key] = value
    return details

def extract_employment_history(text):
    history = []
    # Find all date ranges
    date_pattern = r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})"
    matches = re.findall(date_pattern, text)

    # Find all industries
    industries = re.findall(r"(Construction|Marine|Services|Other)", text, re.IGNORECASE)

    # Find employer labels
    employers = re.findall(r"Employer\s*\d+", text, re.IGNORECASE)

    for i, (start_date, end_date) in enumerate(matches):
        employer = employers[i] if i < len(employers) else f"Employer {i+1}"
        industry = industries[i] if i < len(industries) else "Unknown"
        history.append({
            "Employer": employer,
            "Start_Date": start_date,
            "End_Date": end_date,
            "Industry": industry.capitalize()
        })
    return history

@app.route('/ocr', methods=['POST'])
def ocr():
    print("Incoming keys:", request.files.keys())

    if len(request.files) == 0:
        return jsonify({"error": "No file uploaded"}), 400

    file = next(iter(request.files.values()))
    image = Image.open(file.stream)
    text = pytesseract.image_to_string(image)

    worker_details = extract_worker_details(text)
    employment_history = extract_employment_history(text)

    response = {
        "Worker_Details": worker_details,
        "Employment_History": employment_history,
        "raw_text": text
    }

    return jsonify(response)

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)