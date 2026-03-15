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

# Initialize authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 2. RENDER LOGIN WIDGET
# Wrapping in try-except to catch KeyError 'name' from malformed/stale cookies
try:
    # login returns a tuple: (name, authentication_status, username)
    name, auth_status, username = authenticator.login('main', 'main')
except KeyError:
    st.info("Session expired or invalid cookie. Please log in again.")
    auth_status = None

# 3. DASHBOARD LOGIC
if st.session_state.get("authentication_status"):
    BACKEND_URL = "http://127.0.0.1:5000"
    
    # Use session state with a fallback to avoid KeyErrors during rendering
    current_user_name = st.session_state.get('name', 'User')

    # Sidebar Header & Branding
    st.sidebar.write(f'Welcome, *{current_user_name}*')
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
                headers = {'Content-Type': 'application/json'}
                payload = {"variety": variety, "district": district, "ward": ward}
                res = requests.post(f"{BACKEND_URL}/predict_yield", json=payload, headers=headers, timeout=5)
                
                if res.status_code == 200:
                    st.session_state.forecast = res.json()
                else:
                    st.error(f"Backend Error {res.status_code}: Server rejected request.")
            except Exception as e:
                st.error(f"Connection Failed: Ensure Flask is running on {BACKEND_URL}")

    if st.session_state.get('forecast'):
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
        map_res = requests.get(f"{BACKEND_URL}/get_trends", params={"district": district}, timeout=3)
        if map_res.status_code == 200:
            raw_data = map_res.json().get("data", [])
            if raw_data:
                m_df = pd.DataFrame(raw_data)
                m_df['lat'] = -20.30 + (m_df.index * 0.005)
                m_df['lon'] = 28.85 + (m_df.index * 0.005)
                st.map(m_df[['lat', 'lon']])
                st.success(f"📍 Showing {len(m_df)} active field reports in {district}.")
            else:
                st.info(f"📅 No field reports recorded for {district} yet.")
    except Exception as e:
        st.warning("Map Engine Offline: Check backend connection.")

    st.divider()

    # --- SECTION 3: CSV ANALYSIS & SOIL DIAGNOSTIC ---
    st.header("📂 Smart Field Data Upload")
    uploaded_file = st.file_uploader("Upload Field Log (CSV)", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.subheader("🔍 Data Preview")
        st.dataframe(df.head(3), use_container_width=True)

        if st.button("Analyze & Verify Decision"):
            with st.spinner("Processing against District Benchmarks..."):
                try:
                    # getvalue() ensures the file pointer is at the start and data is correctly read
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/csv')}
                    payload = {'district': district, 'ward': ward, 'variety': variety}
                    res = requests.post(f"{BACKEND_URL}/analyze_csv", files=files, data=payload)
                    
                    if res.status_code == 200:
                        result = res.json()
                        
                        if result["decision"] == "Optimal":
                            st.balloons()
                            st.success(f"### Result: {result['decision']}")
                        else:
                            st.error(f"### Result: {result['decision']}")
                            for alert in result.get("alerts", []):
                                st.warning(alert)

                        st.subheader("🧪 Soil Health Diagnostic")
                        avg_ph = result.get("summary", {}).get("avg_ph", 6.0)
                        ph_options = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
                        nearest_ph = min(ph_options, key=lambda x: abs(x - avg_ph))
                        st.select_slider("Mean Soil pH Level", options=ph_options, value=nearest_ph)

                        if 'Soil_Moisture' in df.columns:
                            st.line_chart(df['Soil_Moisture'])

                        st.divider()
                        st.subheader("📄 Dissemination")
                        report_text = f"ADVISORY REPORT\nDistrict: {district}\nStatus: {result['decision']}\nAvg pH: {avg_ph}"
                        st.download_button(
                            label="📥 Download Advice Slip",
                            data=report_text,
                            file_name=f"Advice_{ward}.txt",
                            mime="text/plain"
                        )
                except Exception as e:
                    st.error(f"Connection Error: {e}")

elif st.session_state.get("authentication_status") is False:
    st.error('Username/password is incorrect')
elif st.session_state.get("authentication_status") is None:
    st.warning('Please enter your username and password')

# --- FOOTER ---
st.divider()
st.caption(f"Deployment | Zimbabwe Agritex AI | Active User: {st.session_state.get('name', 'Guest')}")