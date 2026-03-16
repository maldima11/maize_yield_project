import streamlit as st
import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import os
import numpy as np

# ─────────────────────────────────────────────
# 0. PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Agritex Maize AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# 1. GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
:root {
    --earth-dark:   #0D2B0F;
    --earth-mid:    #1B5E20;
    --earth-bright: #2E7D32;
    --leaf:         #4CAF50;
    --soil:         #6D4C41;
    --gold:         #F9A825;
    --cream:        #F5F0E8;
    --text-dark:    #1A1A1A;
    --text-light:   #888888;
    --danger:       #C62828;
    --card-shadow:  0 4px 24px rgba(0,0,0,0.08);
    --card-radius:  16px;
}

*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: var(--cream);
    font-family: 'DM Sans', sans-serif;
    color: var(--text-dark);
}

/* FIX #2: Hide only the menu/footer, NOT the header collapse button */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* Keep the sidebar collapse toggle arrow visible */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    background: var(--earth-bright) !important;
    border-radius: 0 8px 8px 0 !important;
    color: white !important;
    box-shadow: 2px 0 8px rgba(0,0,0,0.2) !important;
}
[data-testid="collapsedControl"] svg {
    fill: white !important;
    stroke: white !important;
}

.block-container { padding: 2rem 2.5rem 3rem; max-width: 1400px; }

/* ── SIDEBAR BACKGROUND ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #0D2B0F 0%, #1B5E20 55%, #2E7D32 100%) !important;
    border-right: none !important;
    min-width: 260px !important;
}

/* FIX #1: Force ALL sidebar text white using broad selectors */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Sidebar selectbox styling */
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 10px !important;
    color: white !important;
}
section[data-testid="stSidebar"] .stSelectbox svg {
    fill: white !important;
}

/* Sidebar selectbox label */
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSelectbox label p {
    color: rgba(255,255,255,0.75) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* Sidebar divider */
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2) !important;
    margin: 0.8rem 0 !important;
}

/* Sidebar logout button */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.12) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    font-family: 'DM Sans', sans-serif !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.22) !important;
    border-color: rgba(255,255,255,0.5) !important;
}

/* ── PAGE HEADER ── */
.page-header {
    margin-bottom: 1.8rem;
    padding-bottom: 1.2rem;
    border-bottom: 2px solid rgba(46,125,50,0.15);
}
.page-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.1rem; font-weight: 900;
    color: var(--earth-dark); line-height: 1.15; margin: 0;
}
.page-sub { font-size: 0.9rem; color: var(--text-light); margin-top: 0.3rem; }
.live-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #E8F5E9; border: 1px solid #A5D6A7;
    color: var(--earth-bright); font-size: 0.75rem; font-weight: 600;
    padding: 6px 14px; border-radius: 999px;
    letter-spacing: 0.05em; margin-top: 0.6rem;
}
.live-dot {
    width: 7px; height: 7px; background: var(--leaf);
    border-radius: 50%; animation: pulse 1.8s infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50% { opacity:0.4; transform:scale(1.5); }
}

/* ── KPI CARDS ── */
.kpi-card {
    background: white; border-radius: var(--card-radius);
    padding: 1.4rem 1.6rem; box-shadow: var(--card-shadow);
    border-left: 4px solid var(--leaf);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 32px rgba(0,0,0,0.12); }
.kpi-card.warning { border-left-color: var(--gold); }
.kpi-card.danger  { border-left-color: var(--danger); }
.kpi-card.soil    { border-left-color: var(--soil); }
.kpi-label {
    font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.12em; color: var(--text-light);
    font-weight: 600; margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem; font-weight: 700;
    color: var(--earth-dark); line-height: 1.1;
}
.kpi-delta { font-size: 0.8rem; color: var(--leaf); font-weight: 600; margin-top: 0.3rem; }
.kpi-delta.neg { color: var(--danger); }

/* ── SECTION TITLE ── */
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem; font-weight: 700;
    color: var(--earth-dark); margin-bottom: 1rem;
    display: flex; align-items: center; gap: 8px;
}

/* ── MAIN BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, var(--earth-bright) 0%, var(--leaf) 100%) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; font-size: 0.9rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 12px rgba(46,125,50,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(46,125,50,0.4) !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: #F8FBF8 !important;
    border: 2px dashed #A5D6A7 !important;
    border-radius: 14px !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: white; border-radius: 12px;
    padding: 1rem 1.2rem; box-shadow: var(--card-shadow);
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important; text-transform: uppercase !important;
    letter-spacing: 0.1em !important; color: var(--text-light) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.6rem !important; color: var(--earth-dark) !important;
}

hr { border-color: rgba(46,125,50,0.12) !important; margin: 1.5rem 0 !important; }

/* ── DOWNLOAD BUTTON ── */
[data-testid="stDownloadButton"] > button {
    background: white !important; color: var(--earth-bright) !important;
    border: 2px solid var(--earth-bright) !important;
    border-radius: 12px !important; font-weight: 600 !important;
    box-shadow: none !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: var(--earth-bright) !important;
    color: white !important;
    transform: translateY(-1px) !important;
}

/* ── FOOTER ── */
.app-footer {
    text-align: center; padding: 2rem 0 1rem;
    color: var(--text-light); font-size: 0.78rem;
    border-top: 1px solid rgba(46,125,50,0.1); margin-top: 2rem;
}
.app-footer strong { color: var(--earth-bright); }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 2. AUTHENTICATION SETUP
# ─────────────────────────────────────────────
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

try:
    authenticator.login('main')
except Exception:
    pass

auth_status  = st.session_state.get('authentication_status')
current_user = st.session_state.get('name', 'Officer')


# ─────────────────────────────────────────────
# 3. LOGIN / ERROR STATES
# ─────────────────────────────────────────────
def render_login_hero():
    st.markdown("""
    <div style="max-width:460px; margin:3rem auto 1rem; text-align:center;
                background:white; border-radius:24px; padding:2.5rem 2rem;
                box-shadow:0 8px 48px rgba(0,0,0,0.1);
                border-top:5px solid #2E7D32;">
        <div style="font-size:3.5rem; margin-bottom:0.6rem;">🌾</div>
        <h1 style="font-family:'Playfair Display',serif; font-size:1.9rem;
                   font-weight:900; color:#0D2B0F; margin:0 0 0.3rem;">
            Agritex Maize AI
        </h1>
        <p style="color:#888; font-size:0.88rem; margin:0 0 1rem;">
            Digital Support Unit — Zimbabwe
        </p>
        <div style="display:inline-block; background:#E8F5E9; color:#2E7D32;
                    font-size:0.7rem; font-weight:700; padding:4px 14px;
                    border-radius:999px; letter-spacing:0.1em;
                    text-transform:uppercase; margin-bottom:0.5rem;">
            🔒 Secure Officer Access
        </div>
    </div>
    """, unsafe_allow_html=True)

if auth_status == False:
    render_login_hero()
    st.error("⚠️ Incorrect username or password. Please try again.")

elif auth_status is None:
    render_login_hero()
    st.info("👋 Welcome! Enter your credentials above to access the dashboard.")


# ─────────────────────────────────────────────
# 4. MAIN DASHBOARD
# ─────────────────────────────────────────────
elif auth_status == True:
    BACKEND_URL = "http://127.0.0.1:5000"

    # ── SIDEBAR — all inline styles for reliability ──
    with st.sidebar:
        # Brand block
        st.markdown(f"""
        <div style="padding:2rem 1.5rem 1.2rem;
                    border-bottom:1px solid rgba(255,255,255,0.15);
                    margin-bottom:1rem;">
            <div style="font-size:2.8rem; margin-bottom:0.4rem;">🌿</div>
            <div style="font-family:'Playfair Display',serif; font-size:1.5rem;
                        font-weight:900; color:white; letter-spacing:0.02em;
                        line-height:1.1;">
                AGRITEX AI
            </div>
            <div style="font-size:0.7rem; color:rgba(255,255,255,0.55);
                        text-transform:uppercase; letter-spacing:0.18em;
                        margin-top:0.3rem;">
                Digital Support Unit
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User pill
        st.markdown(f"""
        <div style="margin:0 1rem 1.2rem; padding:0.8rem 1rem;
                    background:rgba(255,255,255,0.12);
                    border:1px solid rgba(255,255,255,0.2);
                    border-radius:12px;">
            <div style="font-size:0.65rem; text-transform:uppercase;
                        letter-spacing:0.12em; color:rgba(255,255,255,0.5);
                        margin-bottom:0.25rem;">
                Logged in as
            </div>
            <div style="font-weight:600; color:white; font-size:0.95rem;">
                👤 {current_user}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Section label
        st.markdown("""
        <div style="padding:0 1.5rem; font-size:0.65rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:0.15em;
                    color:rgba(255,255,255,0.4); margin-bottom:0.5rem;">
            📍 Field Context
        </div>
        """, unsafe_allow_html=True)

        # Dropdowns
        district = st.selectbox("District", ["Umzingwane", "Mazabuka", "Chirundu", "Guruve"])
        ward     = st.selectbox("Ward", [f"Ward {i}" for i in range(1, 21)])
        variety  = st.selectbox("Maize Variety", ["SC 301", "SC 529", "Pioneer Hybrid"])

        st.markdown("---")

        # System status indicator
        st.markdown("""
        <div style="margin:0 0.5rem 1rem; padding:0.7rem 1rem;
                    background:rgba(76,175,80,0.2);
                    border:1px solid rgba(76,175,80,0.4);
                    border-radius:10px; font-size:0.8rem; color:white;">
            <span style="color:#8BC34A; font-weight:700;">●</span>
            &nbsp; All systems operational
        </div>
        """, unsafe_allow_html=True)

        # Logout
        authenticator.logout('🚪 Logout', 'sidebar')

        # Version tag
        st.markdown("""
        <div style="padding:1.5rem 0 0.5rem; text-align:center;">
            <div style="font-size:0.62rem; color:rgba(255,255,255,0.25);
                        text-transform:uppercase; letter-spacing:0.1em;">
                Agritex AI · v7.0 · 2026
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── PAGE HEADER ──────────────────────────
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">🌾 Maize Intelligence Dashboard</div>
        <div class="page-sub">Strategic overview · {district} — {ward}</div>
        <div class="live-badge">
            <div class="live-dot"></div> LIVE SYSTEM
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI ROW ──────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown("""<div class="kpi-card">
            <div class="kpi-label">District Target</div>
            <div class="kpi-value">1.4 t/ha</div>
            <div class="kpi-delta">▲ +0.2 from last season</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown("""<div class="kpi-card warning">
            <div class="kpi-label">Active Reports</div>
            <div class="kpi-value">24</div>
            <div class="kpi-delta">▲ 4 new this week</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown("""<div class="kpi-card">
            <div class="kpi-label">System Status</div>
            <div class="kpi-value" style="font-size:1.3rem;color:#2E7D32;">✅ Optimal</div>
            <div class="kpi-delta">All sensors online</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown("""<div class="kpi-card soil">
            <div class="kpi-label">Avg Moisture</div>
            <div class="kpi-value">42%</div>
            <div class="kpi-delta neg">▼ -2% vs benchmark</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    # ── ROW 2: MAP + FORECAST ────────────────
    col_map, col_forecast = st.columns([1.5, 1], gap="medium")

    with col_map:
        st.markdown("""<div class="section-title"><span>📍</span> Live Field Intelligence Map</div>""",
                    unsafe_allow_html=True)
        try:
            map_res = requests.get(
                f"{BACKEND_URL}/get_trends",
                params={"district": district}, timeout=3
            )
            if map_res.status_code == 200:
                raw_data = map_res.json().get("data", [])
                if raw_data:
                    m_df = pd.DataFrame(raw_data)
                    m_df['lat'] = -20.30 + (m_df.index * 0.005)
                    m_df['lon'] =  28.85 + (m_df.index * 0.005)
                    st.map(m_df[['lat', 'lon']], zoom=10)
                else:
                    st.info(f"📅 No field reports for **{district}** yet. Upload a CSV to populate the map.")
            else:
                st.error("Could not retrieve map data from backend.")
        except Exception:
            st.warning("⚠️ Map offline — ensure Flask backend is running on port 5000.")

    with col_forecast:
        st.markdown("""<div class="section-title"><span>🔮</span> AI Decision Support</div>""",
                    unsafe_allow_html=True)

        if st.button("⚡ Generate Localized Forecast", use_container_width=True):
            with st.spinner("Consulting AI Engine..."):
                try:
                    payload = {"variety": variety, "district": district, "ward": ward}
                    res = requests.post(f"{BACKEND_URL}/predict_yield", json=payload, timeout=5)
                    if res.status_code == 200:
                        st.session_state.forecast = res.json()
                    else:
                        st.error(f"Backend Error {res.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect — is Flask running on port 5000?")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

        if st.session_state.get('forecast'):
            f = st.session_state.forecast
            st.success(f"**AI Recommendation:**\n\n{f.get('recommendation')}")
            c1, c2 = st.columns(2)
            c1.metric("Yield Estimate", f"{f.get('predicted_yield_kg_ha')} kg/ha")
            c2.metric("Field Status", f.get('interactive_status', 'Stable'))
        else:
            st.markdown("""
            <div style="text-align:center; padding:2.5rem 1rem;
                        background:#F8FBF8; border-radius:14px;
                        border:2px dashed #C8E6C9; margin-top:0.5rem;">
                <div style="font-size:2.5rem; margin-bottom:0.5rem;">🤖</div>
                <div style="font-size:0.85rem; color:#aaa;">
                    Click above to generate<br>an AI-powered yield forecast
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    st.divider()

    # ── ROW 3: CSV UPLOAD + DIAGNOSTICS ─────
    st.markdown("""<div class="section-title">
        <span>📂</span> Field Log Analysis & Soil Diagnostics
    </div>""", unsafe_allow_html=True)

    up_col, diag_col = st.columns([1, 2], gap="medium")

    with up_col:
        uploaded_file = st.file_uploader(
            "Drop your ward field log here",
            type=["csv"],
            help="CSV must contain Soil_Moisture and pH_Level columns"
        )
        template_csv = "Date,Soil_Moisture,pH_Level\n2026-03-15,42.5,6.2\n2026-03-16,40.1,6.4"
        st.download_button(
            label="📄 Download CSV Template",
            data=template_csv,
            file_name="field_log_template.csv",
            mime="text/csv",
            use_container_width=True
        )

        df_preview = None
        if uploaded_file:
            uploaded_file.seek(0)
            df_preview = pd.read_csv(uploaded_file)
            st.markdown("""
            <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase;
                        letter-spacing:0.1em; color:#888; margin:1rem 0 0.4rem;">
                Preview
            </div>""", unsafe_allow_html=True)
            st.dataframe(df_preview.head(3), use_container_width=True, hide_index=True)

            if st.button("🔬 Run Smart Diagnostic", use_container_width=True):
                with st.spinner("Analyzing against district benchmarks..."):
                    try:
                        files   = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/csv')}
                        payload = {'district': district, 'ward': ward, 'variety': variety}
                        res = requests.post(
                            f"{BACKEND_URL}/analyze_csv",
                            files=files, data=payload, timeout=10
                        )
                        if res.status_code == 200:
                            st.session_state.analysis = res.json()
                            st.balloons()
                        else:
                            st.error("Backend refused the analysis request.")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Connection failed — ensure Flask is running.")
                    except Exception as e:
                        st.error(f"Analysis error: {e}")

    with diag_col:
        if st.session_state.get('analysis'):
            result   = st.session_state.analysis
            decision = result.get('decision', 'Unknown')

            if decision == "Optimal":
                st.success(f"### ✅ Field Status: {decision}")
            else:
                st.error(f"### ⚠️ Field Status: {decision}")
                for alert in result.get("alerts", []):
                    st.warning(f"• {alert}")

            avg_ph       = result.get("summary", {}).get("avg_ph", 6.0)
            avg_moisture = result.get("summary", {}).get("avg_moisture", "N/A")

            m1, m2 = st.columns(2)
            m1.metric("Avg Soil Moisture", f"{avg_moisture}%")
            m2.metric("Avg Soil pH", str(avg_ph))

            st.markdown("**🧪 Soil pH Diagnostic**")
            ph_options = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
            nearest_ph = min(ph_options, key=lambda x: abs(x - avg_ph))
            st.select_slider(
                "pH Level Indicator", options=ph_options,
                value=nearest_ph, help="Maize thrives between pH 5.5 and 7.0"
            )

            if avg_ph < 5.5:
                st.error(f"⚠️ Low pH ({avg_ph}) — soil too acidic for {variety}. Apply agricultural lime.")
            elif avg_ph > 7.0:
                st.warning(f"⚠️ High pH ({avg_ph}) — soil becoming alkaline. Monitor nutrient uptake.")
            else:
                st.success(f"✅ pH {avg_ph} is optimal for {variety} root development.")

            if df_preview is not None and 'Soil_Moisture' in df_preview.columns:
                st.markdown("**📈 Moisture Trend**")
                st.line_chart(df_preview['Soil_Moisture'], use_container_width=True, color="#2E7D32")

            st.markdown("---")

            report_text = f"""==========================================
AGRITEX MAIZE ADVISORY REPORT
==========================================
Date:     {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
Officer:  {current_user}
Location: {district} — {ward}
------------------------------------------
CROP DETAILS:
Variety:      {variety}
Field Status: {decision}
------------------------------------------
SOIL DIAGNOSTICS:
Avg Moisture: {avg_moisture}%
Avg pH Level: {avg_ph}
------------------------------------------
AI RECOMMENDATIONS:
"""
            alerts = result.get("alerts", [])
            report_text += "- Conditions are optimal. Continue standard management.\n" if not alerts else \
                           "".join(f"- {a}\n" for a in alerts)
            report_text += """
------------------------------------------
Generated by: Agritex Maize Intelligence AI
Zimbabwe Digital Support Unit © 2026
==========================================
"""
            st.download_button(
                label="📥 Download Advice Slip for Farmer",
                data=report_text,
                file_name=f"Agritex_Advice_{ward}_{pd.Timestamp.now().strftime('%d%m%Y')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            st.info("💡 Share this report via WhatsApp or print for the farmer.")

        else:
            st.markdown("""
            <div style="text-align:center; padding:3rem 2rem;
                        background:#FAFAFA; border-radius:16px;
                        border:2px dashed #E0E0E0; margin-top:0.5rem;">
                <div style="font-size:3rem; margin-bottom:0.8rem;">🌱</div>
                <div style="font-size:1rem; font-weight:600; color:#888; margin-bottom:0.4rem;">
                    No Analysis Yet
                </div>
                <div style="font-size:0.85rem; color:#bbb;">
                    Upload a CSV and click<br>
                    <strong>Run Smart Diagnostic</strong> to see results here
                </div>
            </div>""", unsafe_allow_html=True)

    # ── ROW 4: REGIONAL TRENDS ───────────────
    st.divider()
    st.markdown("""<div class="section-title">
        <span>📊</span> Live Regional Performance Trends
    </div>""", unsafe_allow_html=True)

    @st.cache_data(ttl=30)
    def fetch_trends(district_name):
        try:
            res = requests.get(
                f"{BACKEND_URL}/get_trends",
                params={"district": district_name}, timeout=5
            )
            if res.status_code == 200:
                return res.json().get("data", [])
        except Exception:
            pass
        return []

    try:
        trends_data = fetch_trends(district)
        if trends_data:
            comp_df = pd.DataFrame(trends_data).rename(columns={
                "ward": "Ward", "avg_moisture": "Moisture (%)",
                "avg_ph": "pH Level", "decision": "Last Decision"
            })
            t_col, s_col = st.columns([2.5, 1], gap="medium")
            with t_col:
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
            with s_col:
                if "Last Decision" in comp_df.columns:
                    total   = len(comp_df)
                    crit    = len(comp_df[comp_df['Last Decision'] == 'Action Required'])
                    optimal = total - crit
                    st.metric("Total Wards", total)
                    st.metric("Optimal Wards", optimal)
                    if crit > 0:
                        st.error(f"⚠️ {crit} ward{'s' if crit > 1 else ''} need attention")
                    else:
                        st.success("✅ All wards performing optimally")
        else:
            st.info(f"No trend data for **{district}** yet. Upload CSVs to populate this table.")
    except Exception as e:
        st.warning(f"Could not load regional trends: {e}")

    # ── FOOTER ───────────────────────────────
    st.markdown(f"""
    <div class="app-footer">
        <strong>Zimbabwe Agritex Digital Intelligence System</strong> &nbsp;·&nbsp;
        Active Officer: {current_user} &nbsp;·&nbsp; © 2026 &nbsp;·&nbsp; v7.0
    </div>""", unsafe_allow_html=True)