import json
import os
from database import save_report  # Integrates with your SQLite database

def get_hybrid_advice(variety):
    """Load the biological thresholds used by both USSD and Web Dashboard."""
    config_path = os.path.join(os.path.dirname(__file__), 'hybrid_configs.json')
    try:
        with open(config_path, 'r') as f:
            configs = json.load(f)
        return configs['hybrids'].get(variety, configs['hybrids']['SC 301'])
    except Exception:
        # Fallback if config file is missing
        return {"min_moisture_pct": 35.0, "optimal_ph": [5.5, 6.5], "name": "SC 301"}

def handle_ussd_request(text, session_id, phone_number, service_code):
    """
    Logic for Africa's Talking USSD Gateway.
    'text' is the sequence of user inputs (e.g., '2*1')
    """
    levels = text.split('*')
    
    # --- 1. MAIN MENU ---
    if text == "":
        response = "CON Welcome to Umzingwane Maize AI\n"
        response += "1. Get Yield Forecast\n"
        response += "2. Report Crop Stress\n"
        response += "3. Change Variety"
        return response

    # --- 2. YIELD FORECAST PATH ---
    elif levels[0] == "1":
        advice = get_hybrid_advice("SC 301")
        response = f"END Forecast for {advice.get('name', 'SC 301')}:\n"
        response += "Target: 1.4t/ha.\n"
        response += f"Tip: Keep moisture above {advice['min_moisture_pct']}%."
        return response

    # --- 3. STRESS REPORTING PATH (With Database Integration) ---
    elif levels[0] == "2":
        if len(levels) == 1:
            response = "CON Select Stress Type:\n"
            response += "1. Leaves Wilting\n"
            response += "2. Yellowing\n"
            response += "3. Pests"
            return response
        
        # Determine Stress Type and AI Advice
        if levels[1] == "1":
            stress_type = "Moisture Stress"
            ai_advice = "Apply mulch and irrigate if possible."
        elif levels[1] == "2":
            stress_type = "Nutrient Stress"
            ai_advice = "Apply Ammonium Nitrate top-dressing."
        elif levels[1] == "3":
            stress_type = "Pest Attack"
            ai_advice = "Check for Armyworm. Apply Lambda-cyhalothrin."
        else:
            return "END Invalid selection."

        # LOG TO DATABASE: Updates the Web Dashboard Map & Trends Table
        # We use "USSD Report" as the ward so extension officers can filter it
        try:
            save_report(
                district="Umzingwane", 
                ward="USSD Report", 
                variety="SC 301", 
                moisture=0.0, 
                ph=0.0, 
                decision=f"USSD Alert: {stress_type}"
            )
        except Exception as e:
            print(f"Database logging failed: {e}")

        return f"END {stress_type} Logged.\nAdvice: {ai_advice}\nAgritex notified for {phone_number}."

    # --- 4. VARIETY SELECTION ---
    elif levels[0] == "3":
        return "END Feature coming soon: You will be able to switch between SC 301, SC 529, and Pioneer."

    else:
        return "END Invalid option. Please try again."