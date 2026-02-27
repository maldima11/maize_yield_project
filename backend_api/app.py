from flask import Flask, request, jsonify

app = Flask(__name__)

# A simple route to check if the server is running
@app.route('/', methods=['GET'])
def home():
    return "Maize Yield Prediction API is running!"

# The main endpoint that your Mobile App and USSD system will communicate with
@app.route('/predict_yield', methods=['POST'])
def mock_predict():
    # Parse incoming JSON data (e.g., from the mobile app or USSD gateway)
    data = request.get_json() or {}
    
    # Extract the maize variety from the request, defaulting to SC 301 if not provided
    variety = data.get('variety', 'SC 301')
    
    # Generate a mock response based on established Zimbabwean agronomic benchmarks
    mock_response = {
        "status": "success",
        "variety": variety,
        "predicted_yield_kg_ha": 1450.5,
        "recommendation": f"Your {variety} crop is entering the V6-V8 leaf stage. Apply Ammonium Nitrate (AN) top-dressing fertilizer now to maximize cob development.",
        "weather_alert": "Forecast shows no severe dry spells in the next 10 days. Moisture levels are optimal."
    }
    
    return jsonify(mock_response)

if __name__ == '__main__':
    # Run the server on port 5000 with debug mode enabled for easier troubleshooting
    app.run(debug=True, port=5000)