from flask import Flask, request, jsonify, make_response
import io
import json
import os
import pandas as pd
from ussd_handler import handle_ussd_request
# Import our new database helper functions
from database import init_db, save_report, get_regional_summary

app = Flask(__name__)

# --- DATABASE INITIALIZATION ---
# This creates the .db file and tables if they don't exist yet
init_db()

# --- CONFIGURATION LOADER ---
def load_configs():
    """Load the biological and regional thresholds from JSON."""
    config_path = os.path.join(os.path.dirname(__file__), 'hybrid_configs.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "hybrids": {"SC 301": {"optimal_ph": [5.5, 6.5], "min_moisture_pct": 35.0}},
            "districts": {"Umzingwane": {"name": "Umzingwane"}}
        }

CONFIGS = load_configs()

@app.route('/', methods=['GET'])
def home():
    return "Maize Yield Prediction API (Phase 7: Database Integrated) is running!"

# --- CSV VALIDATION & DECISION ENGINE ---
@app.route('/analyze_csv', methods=['POST'])
def analyze_csv():
    district_name = request.form.get('district', 'Umzingwane')
    hybrid_name = request.form.get('variety', 'SC 301')
    ward = request.form.get('ward', 'General Ward')

    hybrid_rules = CONFIGS['hybrids'].get(hybrid_name, CONFIGS['hybrids'].get('SC 301'))

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files['file']
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        df = pd.read_csv(stream)

        required_columns = ['Soil_Moisture', 'pH_Level']
        if not all(col in df.columns for col in required_columns):
            return jsonify({
                "status": "error",
                "message": f"Missing columns. CSV must have: {required_columns}"
            }), 400

        alerts = []
        avg_moisture = df['Soil_Moisture'].mean()
        min_moisture = hybrid_rules['min_moisture_pct']
        if avg_moisture < min_moisture:
            alerts.append(f"Low moisture: Avg is {avg_moisture:.1f}% for {hybrid_name}.")

        avg_ph = df['pH_Level'].mean()
        ph_range = hybrid_rules['optimal_ph']
        if avg_ph < ph_range[0] or avg_ph > ph_range[1]:
            alerts.append(f"pH Imbalance: Avg is {avg_ph:.1f} for {hybrid_name}.")

        decision = "Optimal" if not alerts else "Action Required"

        # --- DATABASE INTEGRATION: SAVE THE REPORT ---
        # This saves the result so the dashboard can see historical trends
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

# --- TRENDS ENDPOINT (For Dashboard Regional Table) ---
@app.route('/get_trends', methods=['GET'])
def get_trends():
    district = request.args.get('district', 'Umzingwane')
    try:
        # Fetch aggregated data from SQLite
        df = get_regional_summary(district)
        return jsonify({"status": "success", "data": df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- PREDICT YIELD ENDPOINT ---
@app.route('/predict_yield', methods=['POST'])
def predict():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    variety = data.get('variety', 'SC 301')
    district = data.get('district', 'General')

    return jsonify({
        "status": "success",
        "variety": variety,
        "district": district,
        "predicted_yield_kg_ha": 1450.5,
        "recommendation": f"Your {variety} in {district} is at V6 stage. Apply Top-dressing.",
        "interactive_status": "Green"
    })

# --- USSD ENDPOINT ---
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    if not request.values:
        return make_response("Bad Request", 400)

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
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, port=5000)