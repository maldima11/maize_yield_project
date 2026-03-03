from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Maize Yield Prediction API is running!"

# Your previous Mock API endpoint
@app.route('/predict_yield', methods=['POST'])
def mock_predict():
    data = request.get_json() or {}
    variety = data.get('variety', 'SC 301')
    mock_response = {
        "status": "success",
        "variety": variety,
        "predicted_yield_kg_ha": 1450.5,
        "recommendation": f"Your {variety} crop is entering the V6-V8 leaf stage. Apply Ammonium Nitrate top-dressing now.",
        "weather_alert": "Forecast shows no severe dry spells in the next 10 days. Moisture levels are optimal."
    }
    return jsonify(mock_response)

# --- USSD ENDPOINT ---
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    # Read the variables sent via POST from the Africa's Talking API
    session_id = request.values.get("sessionId", None)
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "")

    # USSD Logic: 'text' contains the string of inputs separated by '*' (e.g., "1*2")
    if text == "":
        # This is the first request. "CON" means the session continues.
        response  = "CON Welcome to the Maize Yield Predictor\n"
        response += "1. Check SC 301 Forecast\n"
        response += "2. Check SC 529 Forecast\n"
        response += "3. Report Crop Stress"

    elif text == "1":
        # The user selected option 1. "END" means the session terminates.
        response = "END Forecast for SC 301: 1450 kg/ha.\nRecommendation: Apply Ammonium Nitrate top-dressing now."

    elif text == "2":
        # The user selected option 2.
        response = "END Forecast for SC 529: 1600 kg/ha.\nRecommendation: Adequate moisture detected. No action needed."

    elif text == "3":
        # The user selected option 3, opening a sub-menu.
        response  = "CON Select stress type:\n"
        response += "1. Drought\n"
        response += "2. Fall Armyworm"

    elif text == "3*1":
        # User selected 3, then 1
        response = "END Drought reported. Recommendation: Apply mulch to retain soil moisture."

    elif text == "3*2":
        # User selected 3, then 2
        response = "END Fall Armyworm reported. Recommendation: Crush visible larvae or apply Lambda-cyhalothrin."

    else:
        response = "END Invalid input. Please try again."

    # Africa's Talking requires the response to be sent as plain text
    res = make_response(response, 200)
    res.headers["Content-Type"] = "text/plain"
    return res

if __name__ == '__main__':
    app.run(debug=True, port=5000)