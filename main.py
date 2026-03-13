from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import os
import re

app = Flask(__name__)

# Windows only: set Tesseract path
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_worker_details(text):
    details = {}
    patterns = {
        "WP_No": r"WP\s*No[:\s]*([A-Z0-9]+)",
        "Name": r"Name\s*(?:of\s*Worker)?[:\s]*([A-Za-z\s]+)(?=\n|$)",
        "Date_of_Birth": r"(?:DOB|Date\s*of\s*Birth)\s*(?:of\s*Worker)?[:\s]*([0-9/]+)",
        "Sex": r"Sex[:\s]*([A-Za-z]+)",
        "FIN": r"(?:FIN|Worker's\s*FIN)[:\s]*([A-Z0-9]+)",
        "Passport_No": r"Passport\s*No[:\s]*([A-Z0-9]+)",
        "Nationality": r"(?:Nationality|Citizenship)[^:]*[:\s]*([A-Za-z]+)"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            details[key] = match.group(1).strip()
    return details

def extract_employment_history(text):
    history = []
    # Find all date ranges
    date_pattern = r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})"
    matches = re.findall(date_pattern, text)

    # Find all industries
    industries = re.findall(r"(Construction|Marine|Services|Other)", text, re.IGNORECASE)

    for i, (start_date, end_date) in enumerate(matches):
        industry = industries[i] if i < len(industries) else "Unknown"
        history.append({
            "Employer": f"Employer {i+1}",
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

    # Ordered response: Worker_Details → Employment_History → raw_text
    response = {
        "Worker_Details": worker_details,
        "Employment_History": employment_history,
        "raw_text": text
    }

    return jsonify(response)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)