import streamlit as st
import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# 1. Load Authentication Configurations
import os
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 2. Render the Login Widget
authenticator.login('main')
name = st.session_state.get('name')
authentication_status = st.session_state.get('authentication_status')
username = st.session_state.get('username')

if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
elif authentication_status == True:
    # --- SECURE DASHBOARD CONTENT STARTS HERE ---
    st.sidebar.write(f'Welcome, *{name}*')
    authenticator.logout('Logout', 'sidebar')

    st.title("🌾 Umzingwane Maize Yield Prediction Dashboard")
    st.markdown("Interactive AI dashboard for Agritex extension officers and policymakers.")

    st.sidebar.header("Administrative Filters")
    ward = st.sidebar.selectbox("Select Ward",)
    variety = st.sidebar.selectbox("Select Maize Variety",)

    st.header(f"Live Yield Forecast: {ward}")
    
    if st.button("Generate Forecast"):
        try:
            # IMPORTANT: Replace with your actual Ngrok URL or deployed Flask URL
            api_url = "https://YOUR-NGROK-URL.ngrok-free.dev/predict_yield"
            
            response = requests.post(api_url, json={"variety": variety})
            
            if response.status_code == 200:
                data = response.json()
                col1, col2, col3 = st.columns(3)
                col1.metric("Predicted Yield", f"{data['predicted_yield_kg_ha']} kg/ha")
                col2.metric("Selected Variety", data['variety'])
                col3.metric("System Status", "Optimal")
                
                st.info(f"**Agronomic Recommendation:** {data['recommendation']}")
                if 'weather_alert' in data:
                    st.warning(f"**Weather Alert:** {data['weather_alert']}")
            else:
                st.error("Error: Failed to fetch data from the API.")
        except Exception as e:
            st.error(f"Connection Error: {e}")

    st.divider()
    st.header("📂 Batch Data Upload & Analysis")
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        if 'Date' in df.columns and 'Yield' in df.columns:
            st.subheader("Yield Trend Analysis")
            df = pd.to_datetime(df)
            chart_data = df.set_index('Date')
            st.line_chart(chart_data)