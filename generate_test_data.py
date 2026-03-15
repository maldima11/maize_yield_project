import pandas as pd
import os

OUTPUT_DIR = '.'  # Change this to your desired folder, e.g. '/data/output'

# 1. Generate "Optimal" Data (Healthy)
healthy_data = {
    'Date': pd.date_range(start='2026-03-01', periods=5),
    'Soil_Moisture': [45, 48, 44, 46, 47],  # Above 35-40% threshold
    'pH_Level': [6.5, 6.4, 6.5, 6.6, 6.5]
}
healthy_path = os.path.join(OUTPUT_DIR, 'healthy_field.csv')
pd.DataFrame(healthy_data).to_csv(healthy_path, index=False)

# 2. Generate "At Risk" Data (Triggers Alerts)
risk_data = {
    'Date': pd.date_range(start='2026-03-01', periods=5),
    'Soil_Moisture': [38, 32, 28, 25, 22],  # Drops below thresholds
    'pH_Level': [6.2, 6.1, 5.5, 5.4, 5.2]
}
risk_path = os.path.join(OUTPUT_DIR, 'risk_field.csv')
pd.DataFrame(risk_data).to_csv(risk_path, index=False)

print(f"✅ Files saved to: {os.path.abspath(OUTPUT_DIR)}")
print(f"   - healthy_field.csv")
print(f"   - risk_field.csv")