from flask import Flask, request, jsonify, make_response
import io
import csv
import json
import os
import pandas as pd

app = Flask(__name__)

# --- CONFIGURATION LOADER ---
def load_configs():
    """Load the biological and regional thresholds from JSON."""
    config_path = os.path.join(os.path.dirname(__file__), 'hybrid_configs.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback defaults if the file is missing
        return {
            "hybrids": {"SC 301": {"optimal_ph": [5.5, 6.5], "min_moisture_pct": 35.0}},
            "districts": {"Umzingwane": {"name": "Umzingwane"}}
        }

@app.route('/', methods=['GET'])
def home():
    return "Maize Yield Prediction API (Phase 7: Integrated JSON Logic) is running!"

# --- UPDATED: CSV VALIDATION & DECISION ENGINE ---
@app.route('/analyze_csv', methods=['POST'])
def analyze_csv():
    # 1. Capture Metadata from the Dashboard request
    district_name = request.form.get('district', 'Umzingwane')
    hybrid_name = request.form.get('variety', 'SC 301')
    ward = request.form.get('ward', 'General Ward')
    
    # Load the rulebook
    configs = load_configs()
    
    # Get specific rules for the hybrid, default to SC 301 if not found
    hybrid_rules = configs['hybrids'].get(hybrid_name, configs['hybrids'].get('SC 301'))
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    
    file = request.files['file']

    # 2. Read and Validate CSV using Pandas for better handling
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        df = pd.read_csv(stream)
        
        # Check for required columns
        required_columns = ['Soil_Moisture', 'pH_Level']
        if not all(col in df.columns for col in required_columns):
            return jsonify({
                "status": "error", 
                "message": f"Missing columns. CSV must have: {required_columns}"
            }), 400

        # 3. Decision Logic: Compare Data vs. JSON Thresholds
        alerts = []
        
        # Check Average Moisture
        avg_moisture = df['Soil_Moisture'].mean()
        min_moisture = hybrid_rules['min_moisture_pct']
        if avg_moisture < min_moisture:
            alerts.append(f"Low moisture: Avg is {avg_moisture:.1f}% (Required: >{min_moisture}%) for {hybrid_name}.")

        # Check Average pH
        avg_ph = df['pH_Level'].mean()
        ph_range = hybrid_rules['optimal_ph'] # [min, max]
        if avg_ph < ph_range[0] or avg_ph > ph_range[1]:
            alerts.append(f"pH Imbalance: Avg is {avg_ph:.1f} (Optimal {hybrid_name} range: {ph_range[0]}-{ph_range[1]}).")

        # 4. Final Decision Assignment
        decision = "Optimal" if not alerts else "Action Required"
        
        return jsonify({
            "status": "success",
            "district": district_name,
            "ward": ward,
            "hybrid": hybrid_name,
            "decision": decision,
            "alerts": alerts,
            "summary": {
                "avg_moisture": round(avg_moisture, 2),
                "avg_ph": round(avg_ph, 2)
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Processing error: {str(e)}"}), 500

# --- PREDICT YIELD ENDPOINT ---
@app.route('/predict_yield', methods=['POST'])
def predict():
    data = request.get_json() or {}
    variety = data.get('variety', 'SC 301')
    district = data.get('district', 'General')
    
    mock_response = {
        "status": "success",
        "variety": variety,
        "district": district,
        "predicted_yield_kg_ha": 1450.5,
        "recommendation": f"Your {variety} in {district} is at V6 stage. Apply Top-dressing.",
        "interactive_status": "Green"
    }
    return jsonify(mock_response)

# --- USSD ENDPOINT ---
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    text = request.values.get("text", "")

    if text == "":
        response  = "CON Welcome to Maize Yield Predictor\n"
        response += "1. Select District\n"
        response += "2. Quick Forecast"
    elif text == "1":
        response = "CON Choose District:\n1. Umzingwane\n2. Mazabuka"
    else:
        response = "END Feature updating for Phase 7."

    res = make_response(response, 200)
    res.headers["Content-Type"] = "text/plain"
    return res

if __name__ == '__main__':
    app.run(debug=True, port=5000)