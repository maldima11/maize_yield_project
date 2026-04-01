from flask import Flask, request, jsonify, make_response

try:
    from flask_cors import CORS
except ImportError:
    raise ImportError("flask-cors is not installed. Run: pip install flask-cors")

import json
import os
import pandas as pd
from database import init_db, save_report, get_regional_summary

app = Flask(__name__)
CORS(app,
     resources={r"/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization",
                    "ngrok-skip-browser-warning"],
     methods=["GET", "POST", "OPTIONS"],
     supports_credentials=False)

# ── CRITICAL: after_request must NEVER override Content-Type for USSD ────────
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization, ngrok-skip-browser-warning"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["ngrok-skip-browser-warning"]   = "true"
    # Never touch Content-Type here — USSD needs text/plain set in its own route
    return response

# ── OPTIONS preflight handler ─────────────────────────────────────────────────
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    res = make_response('', 204)
    res.headers["Access-Control-Allow-Origin"]  = "*"
    res.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization, ngrok-skip-browser-warning"
    )
    res.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return res

# --- DATABASE INITIALIZATION ---
init_db()

# --- CONFIGURATION LOADER ---
def load_configs():
    config_path = os.path.join(os.path.dirname(__file__), 'hybrid_configs.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "hybrids": {
                "SC 301":         {"optimal_ph": [5.5, 6.5], "min_moisture_pct": 35.0},
                "SC 529":         {"optimal_ph": [5.5, 6.8], "min_moisture_pct": 33.0},
                "Pioneer Hybrid": {"optimal_ph": [5.8, 7.0], "min_moisture_pct": 36.0},
            },
            "districts": {"Umzingwane": {"name": "Umzingwane"}}
        }

CONFIGS = load_configs()


# --- HOME ---
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status":  "active",
        "service": "Agritex Maize AI Backend",
        "version": "7.0"
    })


# --- ERROR HANDLERS ---
@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "message": "Internal server error"}), 500


# --- CSV VALIDATION & DECISION ENGINE ---
@app.route('/analyze_csv', methods=['POST'])
def analyze_csv():
    district_name = request.form.get('district', 'Umzingwane')
    hybrid_name   = request.form.get('variety', 'SC 301')
    ward          = request.form.get('ward', 'General Ward')
    hybrid_rules  = CONFIGS['hybrids'].get(
        hybrid_name, CONFIGS['hybrids'].get('SC 301'))

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files['file']
    try:
        df = pd.read_csv(file)
        required_columns = ['Soil_Moisture', 'pH_Level']
        if not all(col in df.columns for col in required_columns):
            return jsonify({
                "status":  "error",
                "message": f"Missing columns: {required_columns}"
            }), 400

        alerts = []

        avg_moisture = df['Soil_Moisture'].mean()
        min_moisture = hybrid_rules.get('min_moisture_pct', 35.0)
        if avg_moisture < min_moisture:
            alerts.append(
                f"Low moisture: {avg_moisture:.1f}% "
                f"(Required >{min_moisture}% for {hybrid_name})"
            )

        avg_ph   = df['pH_Level'].mean()
        ph_range = hybrid_rules.get('optimal_ph', [5.5, 6.5])
        if avg_ph < ph_range[0] or avg_ph > ph_range[1]:
            alerts.append(
                f"pH Imbalance: {avg_ph:.1f} "
                f"(Optimal {ph_range[0]}–{ph_range[1]} for {hybrid_name})"
            )

        decision = "Optimal" if not alerts else "Action Required"

        save_report(
            district=district_name,
            ward=ward,
            variety=hybrid_name,
            moisture=round(float(avg_moisture), 2),
            ph=round(float(avg_ph), 2),
            decision=decision
        )

        return jsonify({
            "status":   "success",
            "decision": decision,
            "alerts":   alerts,
            "summary": {
                "avg_moisture": round(avg_moisture, 2),
                "avg_ph":       round(avg_ph, 2)
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- TRENDS ENDPOINT ---
@app.route('/get_trends', methods=['GET'])
def get_trends():
    district = request.args.get('district', 'Umzingwane')
    try:
        df = get_regional_summary(district)
        return jsonify({
            "status": "success",
            "data":   df.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- PREDICT YIELD ENDPOINT ---
@app.route('/predict_yield', methods=['POST'])
def predict():
    data     = request.get_json(silent=True) or {}
    variety  = data.get('variety', 'SC 301')
    district = data.get('district', 'General')
    ward     = data.get('ward', 'General Ward')
    return jsonify({
        "status":                "success",
        "variety":               variety,
        "district":              district,
        "ward":                  ward,
        "predicted_yield_kg_ha": 1450.5,
        "recommendation": (
            f"Your {variety} in {district} ({ward}) is at V6 stage. "
            "Apply top-dressing fertilizer now for optimal yield."
        ),
        "interactive_status": "Optimal"
    })


# --- MOBILE SYNC ENDPOINT ---
@app.route('/sync_field_record', methods=['POST'])
def sync_field_record():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    required = ['officer_name', 'district', 'ward', 'variety',
                'soil_moisture', 'ph_level', 'created_at']
    missing  = [f for f in required if f not in data]
    if missing:
        return jsonify({
            "status":  "error",
            "message": f"Missing fields: {missing}"
        }), 400

    try:
        save_report(
            district=data['district'],
            ward=data['ward'],
            variety=data['variety'],
            moisture=float(data.get('soil_moisture', 0)),
            ph=float(data.get('ph_level', 0)),
            decision="Synced from Mobile"
        )
        return jsonify({
            "status":  "success",
            "message": "Field record synced successfully",
            "officer": data.get('officer_name'),
            "ward":    data.get('ward'),
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- USSD ENDPOINT ────────────────────────────────────────────────────────────
# Africa's Talking requirements:
#   1. Response body must start with CON (continue) or END (terminate)
#   2. Content-Type must be exactly text/plain
#   3. No extra headers that could confuse the AT gateway
@app.route('/ussd', methods=['POST', 'GET'])
def ussd_callback():
    text         = request.values.get("text", "")
    session_id   = request.values.get("sessionId", "")
    phone_number = request.values.get("phoneNumber", "")

    # Log every request so we can see AT reaching Flask
    print(f"USSD | session={session_id} | phone={phone_number} | text='{text}'")

    input_levels = text.split("*") if text else []

    if text == "":
        response_text = (
            "CON Welcome to Agritex AI\n"
            "1. Start Yield Forecast\n"
            "2. Check System Health"
        )
    elif input_levels[0] == "1":
        if len(input_levels) == 1:
            response_text = "CON Enter your District name:"
        elif len(input_levels) == 2:
            response_text = (
                f"CON District: {input_levels[1].title()}\n"
                "Enter Ward number:"
            )
        elif len(input_levels) == 3:
            response_text = (
                f"END Agritex Advisory:\n"
                f"Dist: {input_levels[1].title()} | "
                f"Ward: {input_levels[2]}\n"
                f"Est. Yield: 1450 kg/ha.\n"
                f"Recommendation: Apply Top-dressing."
            )
        else:
            response_text = "END Invalid entry. Please restart."
    elif input_levels[0] == "2":
        response_text = (
            "END System Status: All regional sensors online. "
            "Data synced with Agritex Cloud."
        )
    else:
        response_text = "END Invalid entry. Please restart."

    # Build response with ONLY what AT needs — nothing extra
    res = make_response(response_text, 200)
    res.headers["Content-Type"] = "text/plain"
    res.headers["Cache-Control"] = "no-cache"
    return res


if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, port=5001, host='0.0.0.0')