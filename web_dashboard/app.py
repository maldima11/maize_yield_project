import streamlit as st
import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import os
import numpy as np

# 1. AUTHENTICATION SETUP
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Render Login Widget
authenticator.login('main')
name = st.session_state.get('name')
auth_status = st.session_state.get('authentication_status')

if auth_status == False:
    st.error('Username/password is incorrect')
elif auth_status is None:
    st.warning('Please enter your username and password')
elif auth_status == True:
    BACKEND_URL = "http://127.0.0.1:5000"

    # Sidebar Header & Branding
    st.sidebar.write(f'Welcome, *{name}*')
    authenticator.logout('Logout', 'sidebar')

    st.title("🌾 Umzingwane Maize Yield Dashboard")
    st.markdown("Interactive AI insights for agricultural extension officers.")

    # Sidebar Selectors
    st.sidebar.header("📍 Regional Context")
    district = st.sidebar.selectbox("Select District", ["Umzingwane", "Mazabuka", "Chirundu", "Guruve"])
    ward = st.sidebar.selectbox("Select Ward", [f"Ward {i}" for i in range(1, 21)])
    variety = st.sidebar.selectbox("Select Maize Variety", ["SC 301", "SC 529", "Pioneer Hybrid"])

    # --- SECTION 1: QUICK AI FORECAST ---
    st.header(f"Live Yield Forecast: {district} - {ward}")
    
    if 'forecast' not in st.session_state:
        st.session_state.forecast = None

    if st.button("Generate Forecast"):
        with st.spinner("Consulting AI Engine..."):
            try:
                # Headers included to prevent 403 Forbidden errors
                headers = {'Content-Type': 'application/json'}
                payload = {"variety": variety, "district": district, "ward": ward}
                res = requests.post(f"{BACKEND_URL}/predict_yield", json=payload, headers=headers, timeout=5)
                
                if res.status_code == 200:
                    st.session_state.forecast = res.json()
                else:
                    st.error(f"Backend Error {res.status_code}: The server rejected the request.")
            except Exception as e:
                st.error(f"Connection Failed: Ensure the Flask backend is running on {BACKEND_URL}")

    if st.session_state.forecast:
        f = st.session_state.forecast
        st.success(f"**AI Recommendation:** {f.get('recommendation')}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Predicted Yield", f"{f.get('predicted_yield_kg_ha')} kg/ha")
        c2.metric("Target Variety", f.get('variety'))
        c3.metric("System Status", f.get('interactive_status', 'Optimal'))

    st.divider()

    # --- SECTION 2: LIVE DISTRICT RISK MAP ---
    st.header("🗺️ District Risk Map")
    try:
        # Fetching real data from the database via Backend
        map_res = requests.get(f"{BACKEND_URL}/get_trends", params={"district": district}, timeout=3)
        if map_res.status_code == 200:
            raw_data = map_res.json().get("data", [])
            
            if raw_data:
                m_df = pd.DataFrame(raw_data)
                # Dynamic coordinate generation for visualization (centered on Zimbabwe region)
                m_df['lat'] = -20.30 + (m_df.index * 0.005)
                m_df['lon'] = 28.85 + (m_df.index * 0.005)
                
                st.map(m_df[['lat', 'lon']])
                st.success(f"📍 Showing {len(m_df)} active field reports in {district}.")
            else:
                st.info(f"📅 No field reports recorded for {district} yet.")
        else:
            st.error("Failed to retrieve map data from backend.")
    except Exception as e:
        st.warning("Map Engine Offline: Check backend connection.")

    st.divider()

    # --- SECTION 3: CSV ANALYSIS & SOIL DIAGNOSTIC ---
    st.header("📂 Smart Field Data Upload")
    uploaded_file = st.file_uploader("Upload Field Log (CSV)", type=["csv"])

    if uploaded_file:
        # Load and Preview Data
        df = pd.read_csv(uploaded_file)
        st.subheader("🔍 Data Preview")
        st.dataframe(df.head(3), use_container_width=True)

        if st.button("Analyze & Verify Decision"):
            with st.spinner("Processing against District Benchmarks..."):
                try:
                    # Using getvalue() for robust file transmission
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/csv')}
                    payload = {'district': district, 'ward': ward, 'variety': variety}
                    
                    res = requests.post(f"{BACKEND_URL}/analyze_csv", files=files, data=payload)
                    
                    if res.status_code == 200:
                        result = res.json()
                        
                        # 1. Decision Status & Visual Feedback
                        if result["decision"] == "Optimal":
                            st.balloons()
                            st.success(f"### Result: {result['decision']}")
                        else:
                            st.error(f"### Result: {result['decision']}")
                            for alert in result.get("alerts", []):
                                st.warning(alert)

                        # 2. Soil Health Diagnostic Gauge
                        st.subheader("🧪 Soil Health Diagnostic")
                        avg_ph = result.get("summary", {}).get("avg_ph", 6.0)
                        ph_options = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
                        nearest_ph = min(ph_options, key=lambda x: abs(x - avg_ph))
                        st.select_slider("Mean Soil pH Level", options=ph_options, value=nearest_ph)

                        # 3. Moisture Trend Visualization
                        if 'Soil_Moisture' in df.columns:
                            st.line_chart(df['Soil_Moisture'])
                            st.caption("Moisture trend from uploaded field data.")

                        # 4. DOWNLOADABLE REPORT GENERATOR
                        st.divider()
                        st.subheader("📄 Dissemination")
                        report_text = f"""
==========================================
MAIZE ADVISORY REPORT: {ward}
==========================================
Officer: {name} | District: {district}
Variety: {variety} | Status: {result['decision']}
Avg Soil pH: {avg_ph} | Avg Moisture: {result.get('summary', {}).get('avg_moisture')}%
------------------------------------------
Agritex Digital Support System
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')}
==========================================
"""
                        st.download_button(
                            label="📥 Download Advice Slip",
                            data=report_text,
                            file_name=f"Advice_{ward}_{variety}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error("Analysis Failed: The backend rejected the file format.")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

    # --- FOOTER ---
    st.divider()
    st.caption(f"Deployment | Zimbabwe Agritex AI | Active User: {name}")