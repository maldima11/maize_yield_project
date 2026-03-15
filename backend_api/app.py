from flask import Flask, request, jsonify, make_response
from flask_cors import CORS  # Critical for Streamlit-Flask communication
import io
import json
import os
import pandas as pd
from ussd_handler import handle_ussd_request
from database import init_db, save_report, get_regional_summary

app = Flask(__name__)

# --- THE MAGIC FIX FOR ERROR 403 ---
# This explicitly allows the Streamlit frontend (even if ports change) to access the API.
CORS(app, resources={r"/*": {"origins": "*"}}) 

# --- DATABASE INITIALIZATION ---
init_db()

# --- CONFIGURATION LOADER ---
def load_configs():
    """Load the biological and regional thresholds from JSON."""
    config_path = os.path.join(os.path.dirname(__file__), 'hybrid_configs.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback thresholds if JSON is missing
        return {
            "hybrids": {"SC 301": {"optimal_ph": [5.5, 6.5], "min_moisture_pct": 35.0}},
            "districts": {"Umzingwane": {"name": "Umzingwane"}}
        }

CONFIGS = load_configs()

@app.route('/', methods=['GET'])
def home():
    return "Maize Yield Prediction API (Phase 7.3: CORS Fully Enabled) is running!"

# --- CSV VALIDATION & DECISION ENGINE ---
@app.route('/analyze_csv', methods=['POST'])
def analyze_csv():
    # 1. Capture Metadata from form-data
    district_name = request.form.get('district', 'Umzingwane')
    hybrid_name = request.form.get('variety', 'SC 301')
    ward = request.form.get('ward', 'General Ward')

    hybrid_rules = CONFIGS['hybrids'].get(hybrid_name, CONFIGS['hybrids'].get('SC 301'))

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files['file']
    try:
        # Read the file directly into Pandas
        df = pd.read_csv(file)

        required_columns = ['Soil_Moisture', 'pH_Level']
        if not all(col in df.columns for col in required_columns):
            return jsonify({
                "status": "error", 
                "message": f"Missing columns. CSV must have: {required_columns}"
            }), 400

        # 2. Decision Logic
        alerts = []
        avg_moisture = df['Soil_Moisture'].mean()
        min_moisture = hybrid_rules.get('min_moisture_pct', 35.0)
        
        if avg_moisture < min_moisture:
            alerts.append(f"Low moisture: Avg is {avg_moisture:.1f}% (Min required: {min_moisture}%)")

        avg_ph = df['pH_Level'].mean()
        ph_range = hybrid_rules.get('optimal_ph', [5.5, 6.5])
        
        if avg_ph < ph_range[0] or avg_ph > ph_range[1]:
            alerts.append(f"pH Imbalance: Avg is {avg_ph:.1f} (Optimal: {ph_range[0]}-{ph_range[1]})")

        decision = "Optimal" if not alerts else "Action Required"

        # 3. SAVE TO DATABASE
        save_report(
            district=district_name,
            ward=ward,
            variety=hybrid_name,
            moisture=round(float(avg_moisture), 2),
            ph=round(float(avg_ph), 2),
            decision=decision
        )

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

# --- TRENDS ENDPOINT (For Dashboard Map & Tables) ---
@app.route('/get_trends', methods=['GET'])
def get_trends():
    district = request.args.get('district', 'Umzingwane')
    try:
        df = get_regional_summary(district)
        return jsonify({"status": "success", "data": df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- PREDICT YIELD ENDPOINT ---
@app.route('/predict_yield', methods=['POST'])
def predict():
    # Explicitly handle JSON sent from Streamlit
    data = request.get_json(silent=True) or {}
    variety = data.get('variety', 'SC 301')
    district = data.get('district', 'General')
    
    return jsonify({
        "status": "success",
        "variety": variety,
        "district": district,
        "predicted_yield_kg_ha": 1450.5,
        "recommendation": f"Your {variety} in {district} is at V6 stage. Apply top-dressing.",
        "interactive_status": "Optimal"
    })

# --- USSD ENDPOINT ---
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    if not request.values:
        return make_response("Bad Request: No USSD data", 400)

    response_text = handle_ussd_request(
        text=request.values.get("text", ""),
        session_id=request.values.get("sessionId", ""),
        phone_number=request.values.get("phoneNumber", ""),
        service_code=request.values.get("serviceCode", "")
    )

    res = make_response(response_text, 200)
    res.headers["Content-Type"] = "text/plain"
    return res

if __name__ == '__main__':
    # Start server on Port 5000
    app.run(debug=True, port=5000)