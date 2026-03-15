from flask import Flask, request, jsonify, make_response
import io
import csv

app = Flask(__name__)

# --- GENERALIZATION CONFIGURATION ---
# This dictionary allows the system to work in any district.
# In a production app, this would eventually move to a Database.
DISTRICT_THRESHOLDS = {
    "mazabuka": {"min_moisture": 35, "ideal_ph": (6.0, 7.0), "name": "Mazabuka"},
    "chirundu": {"min_moisture": 45, "ideal_ph": (5.5, 6.8), "name": "Chirundu"},
    "guruve": {"min_moisture": 40, "ideal_ph": (6.0, 7.5), "name": "Guruve"}
}

@app.route('/', methods=['GET'])
def home():
    return "Maize Yield Prediction API (Phase 7: Interactive) is running!"

# --- NEW: CSV VALIDATION & DECISION ENGINE ---
@app.route('/analyze_csv', methods=['POST'])
def analyze_csv():
    # 1. Get metadata from request
    district_key = request.form.get('district', 'mazabuka').lower()
    ward = request.form.get('ward', 'Unknown Ward')
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    
    file = request.files['file']
    thresholds = DISTRICT_THRESHOLDS.get(district_key, DISTRICT_THRESHOLDS['mazabuka'])

    # 2. Read and Validate CSV
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        
        # Checking for required columns
        required_columns = ['Soil_Moisture', 'pH_Level']
        if not all(col in reader.fieldnames for col in required_columns):
            return jsonify({
                "status": "error", 
                "message": f"Invalid CSV format. Required columns: {required_columns}"
            }), 400

        # 3. Simple Logic for "Decision" (Interactive Feedback)
        data_summary = []
        alerts = []
        for row in reader:
            moisture = float(row['Soil_Moisture'])
            ph = float(row['pH_Level'])
            
            if moisture < thresholds['min_moisture']:
                alerts.append(f"Low moisture detected in {ward} ({moisture}%).")
            
            data_summary.append({"moisture": moisture, "ph": ph})

        # 4. Final Response for the Dashboard
        decision = "Optimal" if not alerts else "Action Required"
        return jsonify({
            "status": "success",
            "district": thresholds['name'],
            "ward": ward,
            "decision": decision,
            "alerts": alerts,
            "summary": data_summary[:5]  # Return first 5 rows for the preview table
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- UPDATED PREDICT ENDPOINT ---
@app.route('/predict_yield', methods=['POST'])
def predict():
    data = request.get_json() or {}
    variety = data.get('variety', 'SC 301')
    district = data.get('district', 'General')
    
    # Logic now factors in the district for a more "presentable" result
    mock_response = {
        "status": "success",
        "variety": variety,
        "district": district,
        "predicted_yield_kg_ha": 1450.5,
        "recommendation": f"Your {variety} in {district} is at V6 stage. Apply Top-dressing.",
        "interactive_status": "Green" # For the frontend "Traffic Light"
    }
    return jsonify(mock_response)

# --- USSD ENDPOINT (Kept for Inclusive Dissemination) ---
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    session_id = request.values.get("sessionId", None)
    text = request.values.get("text", "")

    if text == "":
        response  = "CON Welcome to Maize Yield Predictor\n"
        response += "1. Select District\n"
        response += "2. Quick Forecast"
    elif text == "1":
        response = "CON Choose District:\n1. Mazabuka\n2. Chirundu"
    elif text == "1*1":
        response = "END Mazabuka Selected. Average yield for Hybrid X is 1.4t/ha."
    else:
        response = "END Service currently updating for Phase 7."

    res = make_response(response, 200)
    res.headers["Content-Type"] = "text/plain"
    return res

if __name__ == '__main__':
    app.run(debug=True, port=5000)