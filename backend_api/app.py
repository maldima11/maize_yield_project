from flask import Flask, request, jsonify, make_response
import io
import json
import os
import pandas as pd
from ussd_handler import handle_ussd_request

app = Flask(__name__)

# --- FIX #3: Load configs ONCE at startup, not on every request ---
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

CONFIGS = load_configs()  # FIX #3: Loaded once at startup


@app.route('/', methods=['GET'])
def home():
    return "Maize Yield Prediction API (Phase 7: Integrated USSD & JSON Logic) is running!"


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
            alerts.append(
                f"Low moisture: Avg is {avg_moisture:.1f}% "
                f"(Required: >{min_moisture}%) for {hybrid_name}."
            )

        avg_ph = df['pH_Level'].mean()
        ph_range = hybrid_rules['optimal_ph']
        if avg_ph < ph_range[0] or avg_ph > ph_range[1]:
            alerts.append(
                f"pH Imbalance: Avg is {avg_ph:.1f} "
                f"(Optimal {hybrid_name} range: {ph_range[0]}-{ph_range[1]})."
            )

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
    data = request.get_json()

    # FIX #2: Validate that request body is present and is JSON
    if not data:
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400

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
    # FIX #4: Guard against missing Content-Type or empty form data
    if not request.values:
        return make_response("Bad Request: No form data received", 400)

    # FIX #1: Pass all required Africa's Talking USSD parameters to the handler
    session_id = request.values.get("sessionId", "")
    phone_number = request.values.get("phoneNumber", "")
    service_code = request.values.get("serviceCode", "")
    text = request.values.get("text", "")

    response_text = handle_ussd_request(
        text=text,
        session_id=session_id,
        phone_number=phone_number,
        service_code=service_code
    )

    res = make_response(response_text, 200)
    res.headers["Content-Type"] = "text/plain"
    return res


if __name__ == '__main__':
    # FIX #5: Use environment variable to control debug mode safely
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, port=5000)