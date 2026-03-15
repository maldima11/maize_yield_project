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
elif authentication_status is None:  # FIX #4: use 'is None' instead of '== None'
    st.warning('Please enter your username and password')
elif authentication_status == True:
    BACKEND_URL = "http://127.0.0.1:5000"

    st.sidebar.write(f'Welcome, *{name}*')
    authenticator.logout('Logout', 'sidebar')

    st.title("🌾 Umzingwane Maize Yield Dashboard")
    st.markdown("Phase 7: Interactive AI insights for smallholder farmers and extension officers.")

    st.sidebar.header("📍 Regional Context")
    district = st.sidebar.selectbox("Select District", ["Umzingwane", "Mazabuka", "Chirundu", "Guruve"])
    ward = st.sidebar.selectbox("Select Ward", [f"Ward {i}" for i in range(1, 21)])
    variety = st.sidebar.selectbox("Select Maize Variety", ["SC 301", "SC 529", "Pioneer Hybrid"])

    # --- SECTION 1: QUICK AI FORECAST ---
    st.header(f"Live Yield Forecast: {district} - {ward}")

    if st.button("Generate Forecast"):
        try:
            api_url = f"{BACKEND_URL}/predict_yield"
            payload = {"variety": variety, "district": district, "ward": ward}
            response = requests.post(api_url, json=payload)

            if response.status_code == 200:
                data = response.json()
                col1, col2, col3 = st.columns(3)
                col1.metric("Predicted Yield", f"{data['predicted_yield_kg_ha']} kg/ha")
                col2.metric("Target Hybrid", data['variety'])
                col3.metric("System Status", data.get('interactive_status', 'Optimal'))
                st.success(f"**Recommendation:** {data['recommendation']}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

    st.divider()

    # --- SECTION 2: INTERACTIVE CSV DECISION ENGINE ---
    st.header("📂 Smart Field Data Upload")
    uploaded_file = st.file_uploader("Upload Ward Field Log", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.subheader("🔍 Data Preview")
        st.dataframe(df.head(3), use_container_width=True)

        if st.button("Analyze & Verify Decision"):
            with st.spinner("Processing CSV against District Benchmarks..."):
                # FIX #2: use .seek(0) then .read() for consistent file reading
                uploaded_file.seek(0)
                files = {'file': (uploaded_file.name, uploaded_file.read(), 'text/csv')}
                form_data = {'district': district, 'ward': ward, 'variety': variety}

                try:
                    res = requests.post(f"{BACKEND_URL}/analyze_csv", files=files, data=form_data)
                    result = res.json()

                    if result["status"] == "success":
                        # 1. Decision Alert
                        if result["decision"] == "Optimal":
                            st.balloons()
                            st.success(f"### ✅ Result: {result['decision']}")
                        else:
                            st.error(f"### ⚠️ Result: {result['decision']}")
                            for alert in result["alerts"]:
                                st.warning(alert)

                        # 2. Soil Health Gauge
                        st.subheader("🧪 Soil Health Diagnostic")

                        # FIX #5: safely access summary keys with fallback defaults
                        avg_ph = result.get("summary", {}).get("avg_ph", 6.5)
                        avg_moisture = result.get("summary", {}).get("avg_moisture", "N/A")

                        # FIX #1: snap avg_ph to nearest valid slider option to prevent crash
                        ph_options = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
                        nearest_ph = min(ph_options, key=lambda x: abs(x - avg_ph))

                        st.select_slider(
                            "Soil pH Level Indicator",
                            options=ph_options,
                            value=nearest_ph,
                            help="Maize generally thrives between 5.5 and 7.0 pH"
                        )

                        if avg_ph < 5.5:
                            st.error(f"Low pH Detected ({avg_ph}). Soil is too acidic for {variety}. Consider applying Lime.")
                        elif avg_ph > 7.0:
                            st.warning(f"High pH Detected ({avg_ph}). Soil is becoming alkaline. Monitor nutrient uptake.")
                        else:
                            st.success(f"Optimal pH ({avg_ph})! The soil environment is perfect for {variety} roots.")

                        # 3. Moisture Visualization
                        if 'Soil_Moisture' in df.columns:
                            st.line_chart(df['Soil_Moisture'], use_container_width=True)
                            st.caption("Soil Moisture Trend (%) during the reported period.")

                        # --- PRINTABLE ADVICE REPORT ---
                        st.divider()
                        st.subheader("📄 Dissemination")

                        report_content = f"""
==========================================
MAIZE HYBRID ADVISORY REPORT
==========================================
Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
Officer: {name}
Location: {district} - {ward}
------------------------------------------
CROP DETAILS:
Variety: {variety}
Field Status: {result['decision']}
------------------------------------------
SCIENTIFIC SUMMARY:
- Average Soil Moisture: {avg_moisture}%
- Average Soil pH: {avg_ph}
------------------------------------------
AI RECOMMENDATIONS:
"""
                        if not result["alerts"]:
                            report_content += "- Conditions are optimal. Continue standard management.\n"
                        else:
                            for alert in result["alerts"]:
                                report_content += f"- {alert}\n"

                        report_content += """
------------------------------------------
Generated by: Umzingwane Maize Yield AI
==========================================
"""

                        st.download_button(
                            label="📥 Download Advice Slip for Farmer",
                            data=report_content,
                            file_name=f"Maize_Advice_{ward}_{pd.Timestamp.now().strftime('%d%m%Y')}.txt",
                            mime="text/plain",
                            help="Click to generate a text report that can be shared or printed."
                        )
                        st.info("💡 Pro-tip: This report can be shared via WhatsApp or SMS to the farmer.")

                    else:
                        st.error(f"Validation Error: {result['message']}")
                except Exception as e:
                    st.error(f"Server Connection Error: {e}")

    st.sidebar.divider()
    template_data = "Date,Soil_Moisture,pH_Level\n2026-03-15,42.5,6.2"
    st.sidebar.download_button("📥 Download CSV Template", data=template_data, file_name="field_log_template.csv")
    
    # --- SECTION 3: LIVE REGIONAL TRENDS (FETCHED FROM DATABASE) ---
    st.divider()
    st.header("📊 Live Regional Performance Trends")
    st.markdown(f"Real-time status of wards in **{district}** based on AI field reports.")

    try:
        # Fetch live trends from the Backend API
        trends_url = f"{BACKEND_URL}/get_trends"
        trends_res = requests.get(trends_url, params={"district": district})
        
        if trends_res.status_code == 200:
            trends_data = trends_res.json().get("data", [])
            
            if trends_data:
                # Convert JSON response to DataFrame
                comp_df = pd.DataFrame(trends_data)
                
                # Rename columns for professional display
                comp_df.columns = ["Ward Name", "Avg Moisture (%)", "Avg pH Level", "Last Decision"]

                # Layout for Table and Insights
                col_table, col_info = st.columns([2, 1])
                
                with col_table:
                    # Styling: Color code the decision status for policymakers
                    def color_decision(val):
                        color = 'red' if val == 'Action Required' else 'green'
                        return f'color: {color}; font-weight: bold'

                    st.dataframe(
                        comp_df.style.map(color_decision, subset=['Last Decision']),
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col_info:
                    # Dynamic Insight based on the most common status
                    critical_count = len(comp_df[comp_df['Last Decision'] == 'Action Required'])
                    if critical_count > 0:
                        st.error(f"⚠️ **Attention:** {critical_count} ward(s) in {district} require immediate agronomic intervention.")
                    else:
                        st.success(f"✅ **Summary:** All reporting wards in {district} are currently within optimal thresholds.")
            else:
                st.info(f"📅 No field reports have been recorded for **{district}** yet. Upload a CSV above to start tracking regional trends.")
        else:
            st.error("Could not retrieve regional trends from the server.")
            
    except Exception as e:
        st.warning(f"Connection to Trends Engine failed: {e}")

    # --- SYSTEM FOOTER ---
    st.markdown("---")
    st.caption(f"🇿🇼 **Umzingwane Maize AI** | Phase 7.2 Deployment | Active User: {name}")