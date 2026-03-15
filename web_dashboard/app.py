import streamlit as st
import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import os
import numpy as np

# 0. PAGE CONFIGURATION
st.set_page_config(
    page_title="Agritex Maize AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. CSS FOR BRANDING, VISIBILITY & NATURE THEME
st.markdown("""
    <style>
        /* Main background */
        .stApp { background-color: #F1F3F2; }
        
        /* SIDEBAR BRANDING & VISIBILITY */
        section[data-testid="stSidebar"] {
            background-color: #1B5E20 !important;
        }
        
        /* Logo and Title Alignment */
        .sidebar-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        /* Force all sidebar text to be white for legibility */
        section[data-testid="stSidebar"] .stText, 
        section[data-testid="stSidebar"] label, 
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] .stWrite,
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #FFFFFF !important;
        }

        /* Fix specifically for dropdown labels */
        div[data-testid="stSidebar"] .stSelectbox label p {
            color: white !important;
            font-weight: 600;
        }

        /* Metric Card Styling */
        .stMetric { 
            background-color: white; 
            padding: 15px; 
            border-radius: 10px; 
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05); 
        }
        
        /* Main Content Headers */
        h1, h2, h3 { color: #2E7D32 !important; font-weight: 700; }
        
        /* Button Styling */
        .stButton>button {
            background-color: #2E7D32;
            color: white;
            border-radius: 20px;
            border: none;
            transition: 0.3s;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #388E3C;
            transform: scale(1.02);
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTICATION SETUP ---
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Render Login Widget with KeyError safety
try:
    name, auth_status, username = authenticator.login('main', 'main')
except KeyError:
    st.info("🔄 Session reset. Please enter your credentials.")
    auth_status = None

# --- DASHBOARD LOGIC ---
if st.session_state.get("authentication_status"):
    BACKEND_URL = "http://127.0.0.1:5000"
    current_user_name = st.session_state.get('name', 'Officer')
    
    # --- SIDEBAR: AGRITEX BRANDING & INPUTS ---
    LOGO_URL = "https://cdn-icons-png.flaticon.com/512/2510/2510103.png" 
    st.sidebar.image(LOGO_URL, width=80)
    st.sidebar.markdown("# AGRITEX AI")
    st.sidebar.markdown("### Digital Support Unit")
    st.sidebar.markdown("---")
    
    st.sidebar.write(f"**Logged in:** {current_user_name}")
    
    district = st.sidebar.selectbox("Select District", ["Umzingwane", "Mazabuka", "Chirundu", "Guruve"])
    ward = st.sidebar.selectbox("Select Ward", [f"Ward {i}" for i in range(1, 21)])
    variety = st.sidebar.selectbox("Select Maize Variety", ["SC 301", "SC 529", "Pioneer Hybrid"])
    
    st.sidebar.markdown("---")
    authenticator.logout('Logout', 'sidebar')

    # --- TOP ROW: KPI METRICS (Strategic Overview) ---
    st.title("🌾 Maize Yield Intelligence Dashboard")
    st.subheader(f"Strategic Overview: {district} - {ward}")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("District Target", "1.4 t/ha", "0.2")
    kpi2.metric("Active Reports", "24", "4")
    kpi3.metric("System Status", "Optimal", delta_color="normal")
    kpi4.metric("Avg Moisture", "42%", "-2%")

    st.divider()

    # --- MIDDLE ROW: MAP & FORECAST (Side-by-Side) ---
    col_map, col_forecast = st.columns([1.5, 1])

    with col_map:
        st.write("### 📍 Live Field Intelligence")
        try:
            map_res = requests.get(f"{BACKEND_URL}/get_trends", params={"district": district}, timeout=3)
            if map_res.status_code == 200:
                raw_data = map_res.json().get("data", [])
                if raw_data:
                    m_df = pd.DataFrame(raw_data)
                    # Simulated coordinate offsets for visualization
                    m_df['lat'] = -20.30 + (m_df.index * 0.005)
                    m_df['lon'] = 28.85 + (m_df.index * 0.005)
                    st.map(m_df[['lat', 'lon']], zoom=10)
                else:
                    st.info(f"📅 No field reports recorded for {district} yet.")
            else:
                st.error("Failed to retrieve map data.")
        except Exception as e:
            st.warning("⚠️ Map disconnected. Ensure Backend is running.")

    with col_forecast:
        st.write("### 🔮 AI Decision Support")
        if st.button("Generate Localized Forecast"):
            with st.spinner("Consulting AI Engine..."):
                try:
                    payload = {"variety": variety, "district": district, "ward": ward}
                    res = requests.post(f"{BACKEND_URL}/predict_yield", json=payload, timeout=5)
                    if res.status_code == 200:
                        st.session_state.forecast = res.json()
                    else:
                        st.error(f"Backend Error: {res.status_code}")
                except:
                    st.error("Connection to AI Engine failed.")
        
        if st.session_state.get('forecast'):
            f = st.session_state.forecast
            st.success(f"**AI Recommendation:**\n\n{f.get('recommendation')}")
            st.info(f"**Yield Goal:** {f.get('predicted_yield_kg_ha')} kg/ha | **Status:** {f.get('interactive_status', 'Stable')}")

    st.divider()

    # --- BOTTOM ROW: ANALYSIS & DIAGNOSTICS ---
    st.write("### 📂 Field Log Analysis")
    up_col, diag_col = st.columns([1, 2])

    with up_col:
        uploaded_file = st.file_uploader("Drop Field Log (CSV) Here", type=["csv"])
        if uploaded_file:
            # Data Preview
            df_preview = pd.read_csv(uploaded_file)
            st.dataframe(df_preview.head(3), use_container_width=True)
            
            if st.button("Run Smart Diagnostic"):
                with st.spinner("Analyzing against benchmarks..."):
                    try:
                        # getvalue() ensures data is correctly read for the request
                        files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/csv')}
                        payload = {'district': district, 'ward': ward, 'variety': variety}
                        res = requests.post(f"{BACKEND_URL}/analyze_csv", files=files, data=payload)
                        if res.status_code == 200:
                            st.session_state.analysis = res.json()
                            st.balloons()
                        else:
                            st.error("Backend refused analysis.")
                    except:
                        st.error("Backend connection error during analysis.")

    with diag_col:
        if st.session_state.get('analysis'):
            res = st.session_state.analysis
            c_top, c_bot = st.columns(2)
            
            with c_top:
                st.write(f"#### Result: {res['decision']}")
                # Moisture Trend Chart styled in Forest Green
                chart_data = pd.DataFrame(np.random.randn(15, 1), columns=['Moisture %'])
                st.line_chart(chart_data, color="#2E7D32")
            
            with c_bot:
                avg_ph = res.get("summary", {}).get("avg_ph", 6.0)
                st.write(f"**Mean Soil pH:** {avg_ph}")
                ph_options = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
                nearest_ph = min(ph_options, key=lambda x: abs(x - avg_ph))
                st.select_slider("Soil pH Level", options=ph_options, value=nearest_ph)
                
                # Report Dissemination
                report_text = f"ADVISORY REPORT\nOfficer: {current_user_name}\nDistrict: {district}\nStatus: {res['decision']}\nAvg pH: {avg_ph}"
                st.download_button(
                    label="📥 Download Advice Slip",
                    data=report_text,
                    file_name=f"Agritex_Advice_{ward}.txt",
                    mime="text/plain"
                )

    st.markdown("<br><p style='text-align: center; color: grey;'>Zimbabwe Agritex Digital Intelligence System &copy; 2026</p>", unsafe_allow_html=True)

elif auth_status == False:
    st.error('Username/password is incorrect')
elif auth_status is None:
    st.warning('Please enter your credentials to proceed.')

# --- FOOTER ---
st.caption(f"Active User: {st.session_state.get('name', 'Guest')}")