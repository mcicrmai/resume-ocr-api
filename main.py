from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import pytesseract
import os
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Windows only: set Tesseract path
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Helper Functions ---
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
    # Extract Employment History section
    match = re.search(r"Employment History(.*)", text, re.DOTALL | re.IGNORECASE)
    if not match:
        return history

    section = match.group(1)

    # Extract employers
    employers = re.findall(r"Employer\s*\d+", section, re.IGNORECASE)
    employers.reverse()  # Match earliest dates first

    # Extract all dates
    dates = re.findall(r"(\d{2}/\d{2}/\d{4})", section)

    # Extract industries
    industries = re.findall(r"(Construction|Marine|Services|Other)", section, re.IGNORECASE)

    # Pair dates: assume two consecutive dates = start and end
    date_pairs = []
    i = 0
    while i < len(dates):
        start_date = dates[i]
        end_date = dates[i+1] if i+1 < len(dates) else ""
        date_pairs.append((start_date, end_date))
        i += 2

    # Build history
    for idx, employer in enumerate(employers):
        start_date, end_date = date_pairs[idx] if idx < len(date_pairs) else ("","")
        industry = industries[idx] if idx < len(industries) else "Unknown"
        history.append({
            "Employer": employer,
            "Start_Date": start_date,
            "End_Date": end_date,
            "Industry": industry.capitalize()
        })
    return history

# --- Routes ---
@app.route('/ocr', methods=['POST'])
def ocr():
    if len(request.files) == 0:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files.get("file") or next(iter(request.files.values()))
    image = Image.open(file)
    text = pytesseract.image_to_string(image)

    worker_details = extract_worker_details(text)
    employment_history = extract_employment_history(text)

    return jsonify({
        "Worker_Details": worker_details,
        "Employment_History": employment_history,
        "raw_text": text
    })

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

# --- Main ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)