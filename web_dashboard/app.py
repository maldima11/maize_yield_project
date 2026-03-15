import streamlit as st
import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth  # Requires: streamlit-authenticator==0.2.3
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
elif authentication_status is None:
    st.warning('Please enter your username and password')
elif authentication_status == True:
    BACKEND_URL = "http://127.0.0.1:5000"

    st.sidebar.write(f'Welcome, *{name}*')
    authenticator.logout('Logout', 'sidebar')

    st.title("🌾 Umzingwane Maize Yield Dashboard")
    st.markdown("Interactive AI insights for smallholder farmers and extension officers.")

    st.sidebar.header("📍 Regional Context")
    district = st.sidebar.selectbox("Select District", ["Umzingwane", "Mazabuka", "Chirundu", "Guruve"])
    ward = st.sidebar.selectbox("Select Ward", [f"Ward {i}" for i in range(1, 21)])
    variety = st.sidebar.selectbox("Select Maize Variety", ["SC 301", "SC 529", "Pioneer Hybrid"])

    # --- SECTION 1: QUICK AI FORECAST ---
    st.header(f"Live Yield Forecast: {district} - {ward}")

    if 'forecast_data' not in st.session_state:
        st.session_state.forecast_data = None

    if st.button("Generate Forecast"):
        with st.spinner("Consulting AI Engine..."):
            try:
                api_url = f"{BACKEND_URL}/predict_yield"
                payload = {"variety": variety, "district": district, "ward": ward}
                response = requests.post(api_url, json=payload, timeout=5)

                if response.status_code == 200:
                    st.session_state.forecast_data = response.json()
                else:
                    st.error(f"Backend Error {response.status_code}: Could not retrieve forecast.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection Error: Ensure your Flask backend is running on port 5000.")
            except Exception as e:
                st.error(f"Unexpected Error: {e}")

    if st.session_state.forecast_data:
        data = st.session_state.forecast_data
        st.success(f"**Recommendation:** {data.get('recommendation')}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Predicted Yield", f"{data.get('predicted_yield_kg_ha')} kg/ha")
        col2.metric("Target Hybrid", data.get('variety'))
        col3.metric("System Status", data.get('interactive_status', 'Optimal'))

    st.divider()

    # --- SECTION 2: INTERACTIVE CSV DECISION ENGINE ---
    st.header("📂 Smart Field Data Upload")
    uploaded_file = st.file_uploader("Upload Ward Field Log", type=["csv"])

    if uploaded_file is not None:
        # FIX #4: Seek to start before reading into DataFrame so pointer is at position 0
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file)
        st.subheader("🔍 Data Preview")
        st.dataframe(df.head(3), use_container_width=True)

        if st.button("Analyze & Verify Decision"):
            with st.spinner("Processing CSV against District Benchmarks..."):
                # FIX #2: Added timeout to prevent app from hanging
                uploaded_file.seek(0)
                files = {'file': (uploaded_file.name, uploaded_file.read(), 'text/csv')}
                form_data = {'district': district, 'ward': ward, 'variety': variety}

                try:
                    res = requests.post(
                        f"{BACKEND_URL}/analyze_csv",
                        files=files,
                        data=form_data,
                        timeout=10  # FIX #2: timeout added
                    )
                    result = res.json()

                    if result["status"] == "success":
                        if result["decision"] == "Optimal":
                            st.balloons()
                            st.success(f"### ✅ Result: {result['decision']}")
                        else:
                            st.error(f"### ⚠️ Result: {result['decision']}")
                            for alert in result["alerts"]:
                                st.warning(alert)

                        st.subheader("🧪 Soil Health Diagnostic")
                        avg_ph = result.get("summary", {}).get("avg_ph", 6.5)
                        avg_moisture = result.get("summary", {}).get("avg_moisture", "N/A")

                        ph_options = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
                        nearest_ph = min(ph_options, key=lambda x: abs(x - avg_ph))

                        st.select_slider(
                            "Soil pH Level Indicator",
                            options=ph_options,
                            value=nearest_ph,
                            help="Maize thrives between 5.5 and 7.0 pH"
                        )

                        if avg_ph < 5.5:
                            st.error(f"Low pH ({avg_ph}). Soil too acidic. Apply Lime.")
                        elif avg_ph > 7.0:
                            st.warning(f"High pH ({avg_ph}). Soil alkaline. Monitor nutrients.")
                        else:
                            st.success(f"Optimal pH ({avg_ph}) for {variety}!")

                        if 'Soil_Moisture' in df.columns:
                            st.line_chart(df['Soil_Moisture'], use_container_width=True)

                        st.divider()
                        st.subheader("📄 Dissemination")

                        # FIX #5: Restored closing footer to the report
                        report_content = f"""
==========================================
MAIZE HYBRID ADVISORY REPORT
==========================================
Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
Officer: {name}
Location: {district} - {ward}
------------------------------------------
Field Status: {result['decision']}
Avg Moisture: {avg_moisture}% | Avg pH: {avg_ph}
------------------------------------------
AI RECOMMENDATIONS:
"""
                        if not result["alerts"]:
                            report_content += "- Conditions optimal. Continue standard management.\n"
                        else:
                            for alert in result["alerts"]:
                                report_content += f"- {alert}\n"

                        report_content += """
------------------------------------------
Generated by: Umzingwane Maize Yield AI
==========================================
"""
                        st.download_button(
                            label="📥 Download Advice Slip",
                            data=report_content,
                            file_name=f"Advice_{ward}.txt",
                            mime="text/plain"
                        )

                    else:
                        st.error(f"Validation Error: {result['message']}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Connection Error: Ensure your Flask backend is running on port 5000.")
                except Exception as e:
                    st.error(f"Server Connection Error: {e}")

    # --- SECTION 3: LIVE REGIONAL TRENDS ---
    st.divider()
    st.header("📊 Live Regional Performance Trends")

    # FIX #3: Cache trends per district to avoid refetching on every widget interaction
    @st.cache_data(ttl=30)
    def fetch_trends(district_name):
        res = requests.get(
            f"{BACKEND_URL}/get_trends",
            params={"district": district_name},
            timeout=5
        )
        if res.status_code == 200:
            return res.json().get("data", [])
        return []

    try:
        trends_data = fetch_trends(district)

        if trends_data:
            comp_df = pd.DataFrame(trends_data)

            # FIX #1: Rename columns by their actual backend key names, not by position
            comp_df = comp_df.rename(columns={
                "ward": "Ward",
                "avg_moisture": "Moisture (%)",
                "avg_ph": "pH Level",
                "decision": "Last Decision"
            })

            col_table, col_info = st.columns([2, 1])
            with col_table:
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
            with col_info:
                if "Last Decision" in comp_df.columns:
                    crit = len(comp_df[comp_df['Last Decision'] == 'Action Required'])
                    if crit > 0:
                        st.error(f"⚠️ {crit} wards need attention.")
                    else:
                        st.success("✅ All wards optimal.")
        else:
            st.info(f"No trend data for {district} yet. Upload a CSV to populate this section.")

    except requests.exceptions.ConnectionError:
        st.warning("⚠️ Could not load regional trends: Flask backend not reachable.")
    except Exception as e:
        st.warning(f"Could not load regional trends: {e}")

    st.markdown("---")
    st.caption(f"🇿🇼 Umzingwane Maize AI | Active: {name}")