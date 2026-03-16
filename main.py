import os
import re
import pytesseract
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)

# --- ENVIRONMENT DETECTION ---
if os.name == "nt":
    # Local Windows Path
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    # Railway/Linux Path
    pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def extract_worker_details(text):
    details = {}
    patterns = {
        "WP_No": r"WP\s*No\.?\s*[:\s]*([0-9\s]+)",
        "Name": r"Name\s*(?:of\s*Worker)?[:\s]*([A-Z\s]+?)(?=\n|DOB|Date|$)",
        "DOB": r"(?:DOB|Date\s*of\s*Birth|Birth)[^0-9]*([0-9/]{8,10})",
        "Sex": r"Sex\s*[:\s]*([A-Z]+)",
        "FIN": r"FIN\s*[:\s]*([A-Z0-9]+)",
        "Passport_No": r"Passport\s*No\.?\s*[:\s]*([A-Z0-9]+)",
        "Nationality": r"(?:Nationality|Citizenship)[^:]*[:\s_]*([A-Z]+)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if key in ["WP_No", "Passport_No", "FIN"]:
                value = re.sub(r'[^A-Z0-9]', '', value) 
            details[key] = value
    return details

def extract_employment_history(text):
    history = []
    parts = re.split(r"Employment History", text, flags=re.IGNORECASE)
    if len(parts) < 2: return history
    
    section = parts[1]
    employers = re.findall(r"(Employer\s*\d+)", section, re.IGNORECASE)
    dates = re.findall(r"(\d{2}/\d{2}/\d{4})", section)
    industries = re.findall(r"(Construction|Marine|Services|Manufacturing|Other)", section, re.IGNORECASE)

    for i, emp in enumerate(employers):
        d_idx = i * 2
        history.append({
            "Employer": emp.strip(),
            "Start_Date": dates[d_idx] if d_idx < len(dates) else "N/A",
            "End_Date": dates[d_idx+1] if d_idx+1 < len(dates) else "N/A",
            "Industry": industries[i].strip() if i < len(industries) else "Unknown"
        })
    return history

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "OCR API is online on Port 5000"}), 200

@app.route('/ocr', methods=['POST'])
def ocr():
    if not request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = next(iter(request.files.values()))
    try:
        image = Image.open(file).convert('L')
        text = pytesseract.image_to_string(image)
        
        worker_details = extract_worker_details(text)
        employment_history = extract_employment_history(text)
        
        return jsonify({
            "status": "success",
            "Worker_Details": worker_details,
            "Employment_History": employment_history
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Default to 5000 to match Railway dashboard
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)