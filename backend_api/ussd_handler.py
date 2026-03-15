import json
import os

# Helper to load the same rules used by the Web Dashboard
def get_hybrid_advice(variety):
    config_path = os.path.join(os.path.dirname(__file__), 'hybrid_configs.json')
    with open(config_path, 'r') as f:
        configs = json.load(f)
    return configs['hybrids'].get(variety, configs['hybrids']['SC 301'])

def handle_ussd_request(text):
    """
    Logic for Africa's Talking USSD.
    'text' is the string of user inputs (e.g., '1*1')
    """
    levels = text.split('*')
    
    # 1. Main Menu
    if text == "":
        response = "CON Welcome to Maize AI\n"
        response += "1. Get Yield Forecast\n"
        response += "2. Report Crop Stress\n"
        response += "3. Change Variety"
        return response

    # 2. Yield Forecast Path
    elif levels[0] == "1":
        # In a real app, we'd look up the farmer's phone number in a DB
        # For now, we use the hybrid config
        advice = get_hybrid_advice("SC 301")
        response = f"END Forecast for {advice.get('name', 'SC 301')}:\n"
        response += f"Target: 1.4t/ha.\n"
        response += f"Tip: Ensure moisture is above {advice['min_moisture_pct']}%."
        return response

    # 3. Stress Reporting Path (Interactive Sub-menu)
    elif levels[0] == "2":
        if len(levels) == 1:
            response = "CON Select Stress Type:\n"
            response += "1. Leaves Wilting\n"
            response += "2. Yellowing\n"
            response += "3. Pests"
            return response
        
        elif levels[1] == "1":
            response = "END AI Advice: Possible moisture stress. Apply mulch and irrigate if possible."
            return response
        elif levels[1] == "2":
            response = "END AI Advice: Nitrogen deficiency detected. Apply Ammonium Nitrate top-dressing."
            return response
        elif levels[1] == "3":
            response = "END AI Advice: Check for Fall Armyworm. Apply Lambda-cyhalothrin if larvae are visible."
            return response

    # 4. Variety Selection (Saves to session/DB eventually)
    elif levels[0] == "3":
        response = "END Feature coming soon: Updating your variety to SC 529."
        return response

    else:
        return "END Invalid input. Please try again."