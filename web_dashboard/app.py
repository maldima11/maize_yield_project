import streamlit as st
import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import os

# 1. Load Authentication Configurations
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 2. Render Login Widget
authenticator.login('main')
name = st.session_state.get('name')
authentication_status = st.session_state.get('authentication_status')

if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
elif authentication_status == True:
    # --- CONFIGURATION ---
    # Using local port 5000 as per your Flask setup
    BACKEND_URL = "http://127.0.0.1:5000"

    # --- SECURE DASHBOARD CONTENT ---
    st.sidebar.write(f'Welcome, *{name}*')
    authenticator.logout('Logout', 'sidebar')

    st.title("🌾 Umzingwane Maize Yield Dashboard")
    st.markdown("Phase 7: Interactive AI insights for smallholder farmers and extension officers.")

    # --- SIDEBAR: REGIONAL CONTEXT (Generalization) ---
    st.sidebar.header("📍 Regional Context")
    st.sidebar.info("Select the location to calibrate AI thresholds to local soil and climate profiles.")
    
    # Generalizing across districts
    district = st.sidebar.selectbox("Select District", ["Umzingwane", "Mazabuka", "Chirundu", "Guruve"])
    
    # Ward selection with help text
    ward = st.sidebar.selectbox("Select Ward", [f"Ward {i}" for i in range(1, 21)], help="Each ward has unique soil benchmarks.")
    variety = st.sidebar.selectbox("Select Maize Variety", ["SC 301", "SC 529", "Pioneer Hybrid"])

    # --- SECTION 1: QUICK AI FORECAST ---
    st.header(f"Live Yield Forecast: {district} - {ward}")
    
    if st.button("Generate Forecast"):
        try:
            # Pointing to your local Flask predict_yield endpoint
            api_url = f"{BACKEND_URL}/predict_yield"
            payload = {"variety": variety, "district": district, "ward": ward}
            
            response = requests.post(api_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                col1, col2, col3 = st.columns(3)
                col1.metric("Predicted Yield", f"{data['predicted_yield_kg_ha']} kg/ha")
                col2.metric("Target Hybrid", data['variety'])
                # Using the new interactive_status from backend
                status_label = data.get('interactive_status', 'Optimal')
                col3.metric("System Status", status_label)
                
                st.success(f"**Recommendation:** {data['recommendation']}")
            else:
                st.error("Error: Failed to fetch data from the API.")
        except Exception as e:
            st.error(f"Connection Error: {e}")

    st.divider()

    # --- SECTION 2: INTERACTIVE CSV DECISION ENGINE ---
    st.header("📂 Smart Field Data Upload")
    st.markdown("""
    **Instructions:** 1. Select your Ward in the sidebar.
    2. Upload your weekly field readings (.csv).
    3. The AI will validate your data against regional moisture and pH targets.
    """)

    uploaded_file = st.file_uploader("Upload Ward Field Log", type=["csv"], help="CSV must contain: Soil_Moisture, pH_Level")

    if uploaded_file is not None:
        # Show instant preview
        df = pd.read_csv(uploaded_file)
        st.subheader("🔍 Data Preview")
        st.dataframe(df.head(3), use_container_width=True)

        # Analysis Button
        if st.button("Analyze & Verify Decision"):
            with st.spinner("Processing CSV against District Benchmarks..."):
                # Reset file pointer
                uploaded_file.seek(0)
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/csv')}
                form_data = {'district': district, 'ward': ward}

                try:
                    res = requests.post(f"{BACKEND_URL}/analyze_csv", files=files, data=form_data)
                    result = res.json()

                    if result["status"] == "success":
                        # Display Decision Card
                        if result["decision"] == "Optimal":
                            st.balloons()
                            st.success(f"### ✅ Result: {result['decision']}")
                            st.write(f"Current conditions in **{ward}** are ideal for the chosen hybrid.")
                        else:
                            st.error(f"### ⚠️ Result: {result['decision']}")
                            for alert in result["alerts"]:
                                st.warning(alert)
                        
                        # Visualization
                        if 'Soil_Moisture' in df.columns:
                            st.line_chart(df['Soil_Moisture'], use_container_width=True)
                            st.caption("Soil Moisture Trend (%) during the reported period.")

                    else:
                        st.error(f"Validation Error: {result['message']}")
                except Exception as e:
                    st.error(f"Server Connection Error: {e}")

    # Sidebar Footer: Template Download
    st.sidebar.divider()
    template_data = "Date,Soil_Moisture,pH_Level\n2026-03-15,42.5,6.2"
    st.sidebar.download_button(
        label="📥 Download CSV Template",
        data=template_data,
        file_name="field_log_template.csv",
        mime="text/csv"
    )