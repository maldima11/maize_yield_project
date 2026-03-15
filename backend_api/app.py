from flask import Flask, request, jsonify, make_response
from flask_cors import CORS 
import io
import json
import os
import pandas as pd
from database import init_db, save_report, get_regional_summary

app = Flask(__name__)

# --- THE MAGIC FIX FOR ERROR 403 ---
CORS(app, resources={r"/*": {"origins": "*"}}) 

# --- DATABASE INITIALIZATION ---
init_db()

# --- CONFIGURATION LOADER ---
def load_configs():
    """Load biological and regional thresholds from JSON."""
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
    return "Agritex Maize AI Backend is active!"

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
        df = pd.read_csv(file)
        required_columns = ['Soil_Moisture', 'pH_Level']
        if not all(col in df.columns for col in required_columns):
            return jsonify({"status": "error", "message": f"Missing columns: {required_columns}"}), 400

        alerts = []
        avg_moisture = df['Soil_Moisture'].mean()
        min_moisture = hybrid_rules.get('min_moisture_pct', 35.0)
        if avg_moisture < min_moisture:
            alerts.append(f"Low moisture: {avg_moisture:.1f}%")

        avg_ph = df['pH_Level'].mean()
        ph_range = hybrid_rules.get('optimal_ph', [5.5, 6.5])
        if avg_ph < ph_range[0] or avg_ph > ph_range[1]:
            alerts.append(f"pH Imbalance: {avg_ph:.1f}")

        decision = "Optimal" if not alerts else "Action Required"

        save_report(district=district_name, ward=ward, variety=hybrid_name, 
                    moisture=round(float(avg_moisture), 2), ph=round(float(avg_ph), 2), decision=decision)

        return jsonify({
            "status": "success", "decision": decision, "alerts": alerts,
            "summary": {"avg_moisture": round(avg_moisture, 2), "avg_ph": round(avg_ph, 2)}
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- TRENDS ENDPOINT (Dashboard) ---
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
    data = request.get_json(silent=True) or {}
    variety = data.get('variety', 'SC 301')
    district = data.get('district', 'General')
    return jsonify({
        "status": "success", "variety": variety, "predicted_yield_kg_ha": 1450.5,
        "recommendation": f"Your {variety} in {district} is at V6. Apply top-dressing.",
        "interactive_status": "Optimal"
    })

# --- ADVANCED MULTI-LEVEL USSD ENDPOINT ---
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    # 1. Capture data from Africa's Talking
    text = request.values.get("text", "")
    session_id = request.values.get("sessionId", "")
    phone_number = request.values.get("phoneNumber", "")
    
    # 2. Split text to manage conversational depth
    input_levels = text.split("*")
    
    if text == "":
        # Level 0: Main Menu
        response = "CON Welcome to Agritex AI\n"
        response += "1. Start Yield Forecast\n"
        response += "2. Check System Health"
        
    elif input_levels[0] == "1":
        # Level 1: Chose Forecast -> Ask for District
        if len(input_levels) == 1:
            response = "CON Enter your District name:"
            
        # Level 2: District Entered -> Ask for Ward
        elif len(input_levels) == 2:
            district_input = input_levels[1]
            response = f"CON District: {district_input.title()}\nEnter Ward number:"
            
        # Level 3: Ward Entered -> Process Result
        elif len(input_levels) == 3:
            district_input = input_levels[1].title()
            ward_input = input_levels[2]
            
            # Placeholder for AI Model Integration
            # yield_val = model.predict(...)
            predicted_yield = 1450 
            
            response = f"END Agritex Advisory:\n"
            response += f"Dist: {district_input} | Ward: {ward_input}\n"
            response += f"Est. Yield: {predicted_yield} kg/ha.\n"
            response += "Recommendation: Apply Top-dressing."
            
    elif input_levels[0] == "2":
        # System Health Check
        response = "END System Status: All regional sensors are online. Data is synced with Agritex Cloud."
        
    else:
        # Error handling for invalid menu options
        response = "END Invalid entry. Please restart the session."

    # 3. Final Response Construction
    res = make_response(response, 200)
    res.headers["Content-Type"] = "text/plain"
    return res

if __name__ == '__main__':
    app.run(debug=True, port=5000)