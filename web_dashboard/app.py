import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import os

st.set_page_config(
    page_title="Agritex Maize AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS injection via components.html so Streamlit cannot strip the style tag ──
components.html("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root {
    --earth-dark:   #0D2B0F;
    --earth-bright: #2E7D32;
    --leaf:         #4CAF50;
    --soil:         #6D4C41;
    --gold:         #F9A825;
    --cream:        #F5F0E8;
    --text-light:   #888;
    --danger:       #C62828;
    --shadow:       0 4px 24px rgba(0,0,0,0.08);
    --radius:       16px;
}
</style>
<script>
// Inject styles into the parent Streamlit document
const css = `
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap');

.stApp { background: #F5F0E8 !important; font-family: 'DM Sans', sans-serif !important; }
#MainMenu, footer { visibility: hidden !important; }
.block-container { padding: 2rem 2.5rem 3rem !important; max-width: 1400px !important; }

section[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #0D2B0F 0%, #1B5E20 60%, #2E7D32 100%) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding: 1rem 1rem 2rem !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 10px !important;
    color: white !important;
}
section[data-testid="stSidebar"] .stSelectbox svg { fill: white !important; }
section[data-testid="stSidebar"] .stSelectbox label p {
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.74rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.12) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.35) !important;
    border-radius: 10px !important;
    width: 100% !important;
    font-size: 0.85rem !important;
    transition: background 0.2s !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2) !important;
}
/* ── Sidebar collapse/expand toggle ── */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    background: #2E7D32 !important;
    border-radius: 0 8px 8px 0 !important;
    box-shadow: 2px 0 8px rgba(0,0,0,0.2) !important;
    overflow: hidden !important;
}
[data-testid="collapsedControl"] svg {
    fill: white !important;
    stroke: white !important;
}
/* Hide the broken Material icon text (keyboard_double_arrow_left etc) */
[data-testid="stSidebarCollapseButton"] span,
[data-testid="stSidebarCollapseButton"] .material-symbols-rounded {
    font-size: 0 !important;
    visibility: hidden !important;
}
/* Replace with a clean CSS arrow instead */
[data-testid="stSidebarCollapseButton"] button {
    background: #2E7D32 !important;
    border: none !important;
    border-radius: 0 8px 8px 0 !important;
    width: 24px !important;
    height: 48px !important;
    cursor: pointer !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="stSidebarCollapseButton"] button::after {
    content: '‹' !important;
    font-size: 1.4rem !important;
    color: white !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    visibility: visible !important;
    font-family: sans-serif !important;
}
/* Also fix the top-left expand button when sidebar is collapsed */
[data-testid="collapsedControl"] button {
    background: #2E7D32 !important;
    border: none !important;
    width: 24px !important;
    height: 48px !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="collapsedControl"] button span {
    font-size: 0 !important;
    visibility: hidden !important;
}
[data-testid="collapsedControl"] button::after {
    content: '›' !important;
    font-size: 1.4rem !important;
    color: white !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    visibility: visible !important;
    font-family: sans-serif !important;
}

.page-header { margin-bottom: 1.8rem; padding-bottom: 1.2rem; border-bottom: 2px solid rgba(46,125,50,0.15); }
.page-title { font-family: 'Playfair Display', serif !important; font-size: 2rem; font-weight: 900; color: #0D2B0F; margin: 0; }
.page-sub { font-size: 0.88rem; color: #888; margin-top: 0.25rem; }
.live-badge { display: inline-flex; align-items: center; gap: 6px; background: #E8F5E9; border: 1px solid #A5D6A7; color: #2E7D32; font-size: 0.73rem; font-weight: 600; padding: 5px 13px; border-radius: 999px; margin-top: 0.6rem; }
.live-dot { width: 7px; height: 7px; background: #4CAF50; border-radius: 50%; animation: pulse 1.8s infinite; }
@keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.4; transform:scale(1.5); } }

.kpi-card { background: white; border-radius: 16px; padding: 1.3rem 1.5rem; box-shadow: 0 4px 24px rgba(0,0,0,0.08); border-left: 4px solid #4CAF50; transition: transform 0.2s, box-shadow 0.2s; }
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 32px rgba(0,0,0,0.12); }
.kpi-card.gold { border-left-color: #F9A825; }
.kpi-card.soil { border-left-color: #6D4C41; }
.kpi-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.12em; color: #888; font-weight: 600; margin-bottom: 0.4rem; }
.kpi-value { font-family: 'Playfair Display', serif; font-size: 1.9rem; font-weight: 700; color: #0D2B0F; line-height: 1.1; }
.kpi-delta { font-size: 0.78rem; color: #4CAF50; font-weight: 600; margin-top: 0.25rem; }
.kpi-delta.neg { color: #C62828; }

.section-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; color: #0D2B0F; margin-bottom: 0.8rem; }

.stButton > button { background: linear-gradient(135deg, #2E7D32, #4CAF50) !important; color: white !important; border: none !important; border-radius: 12px !important; font-weight: 600 !important; font-family: 'DM Sans', sans-serif !important; box-shadow: 0 4px 12px rgba(46,125,50,0.3) !important; transition: all 0.2s !important; }
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 20px rgba(46,125,50,0.4) !important; }

[data-testid="stFileUploader"] { background: #F8FBF8 !important; border: 2px dashed #A5D6A7 !important; border-radius: 14px !important; }
[data-testid="stMetric"] { background: white; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
[data-testid="stMetricValue"] { font-family: 'Playfair Display', serif !important; font-size: 1.5rem !important; color: #0D2B0F !important; }
[data-testid="stMetricLabel"] { font-size: 0.73rem !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; color: #888 !important; }
[data-testid="stDownloadButton"] > button { background: white !important; color: #2E7D32 !important; border: 2px solid #2E7D32 !important; border-radius: 12px !important; font-weight: 600 !important; box-shadow: none !important; }
[data-testid="stDownloadButton"] > button:hover { background: #2E7D32 !important; color: white !important; }
hr { border-color: rgba(46,125,50,0.12) !important; margin: 1.2rem 0 !important; }
.app-footer { text-align:center; padding: 1.5rem 0 0.5rem; color: #888; font-size: 0.76rem; border-top: 1px solid rgba(46,125,50,0.1); margin-top: 2rem; }
.app-footer strong { color: #2E7D32; }
`;

const style = window.parent.document.createElement('style');
style.innerHTML = css;
window.parent.document.head.appendChild(style);
</script>
""", height=0)

# ── AUTHENTICATION ──
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path) as f:
    config = yaml.load(f, Loader=SafeLoader)

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

# ── LOGIN HERO ──
def login_hero():
    st.markdown("""
    <div style="max-width:440px;margin:3rem auto;text-align:center;
                background:white;border-radius:24px;padding:2.5rem 2rem;
                box-shadow:0 8px 48px rgba(0,0,0,0.1);
                border-top:5px solid #2E7D32;">
        <div style="font-size:3.2rem;margin-bottom:0.5rem;">🌾</div>
        <h1 style="font-family:'Playfair Display',serif;font-size:1.85rem;
                   font-weight:900;color:#0D2B0F;margin:0 0 0.3rem;">
            Agritex Maize AI
        </h1>
        <p style="color:#999;font-size:0.86rem;margin:0 0 1rem;">
            Digital Support Unit — Zimbabwe
        </p>
        <span style="background:#E8F5E9;color:#2E7D32;font-size:0.68rem;
                     font-weight:700;padding:4px 14px;border-radius:999px;
                     letter-spacing:0.1em;text-transform:uppercase;">
            🔒 Secure Officer Access
        </span>
    </div>
    """, unsafe_allow_html=True)

if auth_status == False:
    login_hero()
    st.error("⚠️ Incorrect username or password. Please try again.")

elif auth_status is None:
    login_hero()
    st.info("👋 Welcome! Enter your credentials above to continue.")

elif auth_status == True:
    BACKEND_URL = "http://127.0.0.1:5000"

    # ── SIDEBAR — single with block ──
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:1.2rem 0.5rem 1rem;
                    border-bottom:1px solid rgba(255,255,255,0.15);
                    margin-bottom:1rem;">
            <div style="font-size:2.6rem;line-height:1;">🌿</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.45rem;
                        font-weight:900;color:white;margin-top:0.4rem;">
                AGRITEX AI
            </div>
            <div style="font-size:0.66rem;color:rgba(255,255,255,0.5);
                        text-transform:uppercase;letter-spacing:0.18em;
                        margin-top:0.2rem;">
                Digital Support Unit
            </div>
        </div>
        <div style="background:rgba(255,255,255,0.1);
                    border:1px solid rgba(255,255,255,0.18);
                    border-radius:10px;padding:0.6rem 0.9rem;
                    margin-bottom:1.2rem;">
            <div style="font-size:0.62rem;text-transform:uppercase;
                        letter-spacing:0.1em;color:rgba(255,255,255,0.45);
                        margin-bottom:0.2rem;">Logged in as</div>
            <div style="font-weight:600;color:white;font-size:0.9rem;">
                👤 {current_user}
            </div>
        </div>
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.14em;color:rgba(255,255,255,0.4);
                    margin-bottom:0.4rem;">
            📍 Field Context
        </div>
        """, unsafe_allow_html=True)

        district = st.selectbox("District", ["Umzingwane", "Mazabuka", "Chirundu", "Guruve"])
        ward     = st.selectbox("Ward", [f"Ward {i}" for i in range(1, 21)])
        variety  = st.selectbox("Maize Variety", ["SC 301", "SC 529", "Pioneer Hybrid"])

        st.divider()

        st.markdown("""
        <div style="background:rgba(76,175,80,0.18);border:1px solid rgba(76,175,80,0.35);
                    border-radius:9px;padding:0.6rem 0.9rem;font-size:0.8rem;
                    color:white;margin-bottom:0.8rem;">
            <span style="color:#8BC34A;">●</span> All systems operational
        </div>
        """, unsafe_allow_html=True)

        authenticator.logout("Logout", "sidebar")

        st.markdown("""
        <div style="text-align:center;padding-top:1.5rem;">
            <div style="font-size:0.6rem;color:rgba(255,255,255,0.22);
                        text-transform:uppercase;letter-spacing:0.1em;">
                Agritex AI · v7.0 · 2026
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── PAGE HEADER ──
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">🌾 Maize Intelligence Dashboard</div>
        <div class="page-sub">Strategic overview · {district} — {ward}</div>
        <div class="live-badge"><div class="live-dot"></div>&nbsp;LIVE SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI ROW ──
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown("""<div class="kpi-card">
            <div class="kpi-label">District Target</div>
            <div class="kpi-value">1.4 t/ha</div>
            <div class="kpi-delta">▲ +0.2 from last season</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown("""<div class="kpi-card gold">
            <div class="kpi-label">Active Reports</div>
            <div class="kpi-value">4</div>
            <div class="kpi-delta">▲ 4 new this week</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown("""<div class="kpi-card">
            <div class="kpi-label">System Status</div>
            <div class="kpi-value" style="font-size:1.2rem;color:#2E7D32;">✅ Optimal</div>
            <div class="kpi-delta">All sensors online</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown("""<div class="kpi-card soil">
            <div class="kpi-label">Avg Moisture</div>
            <div class="kpi-value">42%</div>
            <div class="kpi-delta neg">▼ -2% vs benchmark</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

    # ── MAP + FORECAST ──
    col_map, col_forecast = st.columns([1.5, 1], gap="medium")

    with col_map:
        st.markdown('<div class="section-title">📍 Live Field Intelligence Map</div>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{BACKEND_URL}/get_trends", params={"district": district}, timeout=3)
            if r.status_code == 200:
                raw = r.json().get("data", [])
                if raw:
                    mdf = pd.DataFrame(raw)
                    mdf['lat'] = -20.30 + mdf.index * 0.005
                    mdf['lon'] =  28.85 + mdf.index * 0.005
                    st.map(mdf[['lat','lon']], zoom=10)
                else:
                    st.info(f"No field data for **{district}** yet. Upload a CSV to populate the map.")
        except Exception:
            st.warning("⚠️ Map offline — ensure Flask is running on port 5000.")

    with col_forecast:
        st.markdown('<div class="section-title">AI Decision Support</div>', unsafe_allow_html=True)
        if st.button("⚡ Generate Localized Forecast", use_container_width=True):
            with st.spinner("Consulting AI Engine..."):
                try:
                    r = requests.post(f"{BACKEND_URL}/predict_yield",
                                      json={"variety": variety, "district": district, "ward": ward},
                                      timeout=5)
                    if r.status_code == 200:
                        st.session_state.forecast = r.json()
                    else:
                        st.error(f"Backend Error {r.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect — is Flask running on port 5000?")
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.session_state.get('forecast'):
            f = st.session_state.forecast
            st.success(f"**AI Recommendation:** {f.get('recommendation')}")
            c1, c2 = st.columns(2)
            c1.metric("Yield Estimate", f"{f.get('predicted_yield_kg_ha')} kg/ha")
            c2.metric("Field Status", f.get('interactive_status', 'Stable'))
        else:
            st.markdown("""
            <div style="text-align:center;padding:2.5rem 1rem;background:#F8FBF8;
                        border-radius:12px;border:2px dashed #C8E6C9;margin-top:0.5rem;">
                <div style="font-size:2.2rem;margin-bottom:0.4rem;">🤖</div>
                <div style="font-size:0.82rem;color:#aaa;">
                    Click above to generate<br>an AI-powered yield forecast
                </div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # ── CSV UPLOAD + DIAGNOSTICS ──
    st.markdown('<div class="section-title">📂 Field Log Analysis & Soil Diagnostics</div>', unsafe_allow_html=True)
    up_col, diag_col = st.columns([1, 2], gap="medium")

    with up_col:
        uploaded_file = st.file_uploader(
            "Drop your ward field log here", type=["csv"],
            help="CSV must contain Soil_Moisture and pH_Level columns"
        )
        st.download_button(
            "📄 Download CSV Template",
            data="Date,Soil_Moisture,pH_Level\n2026-03-15,42.5,6.2\n2026-03-16,40.1,6.4",
            file_name="field_log_template.csv", mime="text/csv",
            use_container_width=True
        )
        df_preview = None
        if uploaded_file:
            uploaded_file.seek(0)
            df_preview = pd.read_csv(uploaded_file)
            st.caption("Preview")
            st.dataframe(df_preview.head(3), use_container_width=True, hide_index=True)
            if st.button("🔬 Run Smart Diagnostic", use_container_width=True):
                with st.spinner("Analyzing against district benchmarks..."):
                    try:
                        r = requests.post(
                            f"{BACKEND_URL}/analyze_csv",
                            files={'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/csv')},
                            data={'district': district, 'ward': ward, 'variety': variety},
                            timeout=10
                        )
                        if r.status_code == 200:
                            st.session_state.analysis = r.json()
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
            avg_ph       = result.get("summary", {}).get("avg_ph", 6.0)
            avg_moisture = result.get("summary", {}).get("avg_moisture", "N/A")

            if decision == "Optimal":
                st.success(f"### ✅ Field Status: {decision}")
            else:
                st.error(f"### ⚠️ Field Status: {decision}")
                for alert in result.get("alerts", []):
                    st.warning(f"• {alert}")

            m1, m2 = st.columns(2)
            m1.metric("Avg Soil Moisture", f"{avg_moisture}%")
            m2.metric("Avg Soil pH", str(avg_ph))

            st.markdown("**🧪 Soil pH Diagnostic**")
            ph_options = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
            nearest_ph = min(ph_options, key=lambda x: abs(x - avg_ph))
            st.select_slider("pH Level Indicator", options=ph_options,
                             value=nearest_ph, help="Maize thrives between pH 5.5–7.0")

            if avg_ph < 5.5:
                st.error(f"⚠️ Low pH ({avg_ph}) — too acidic for {variety}. Apply agricultural lime.")
            elif avg_ph > 7.0:
                st.warning(f"⚠️ High pH ({avg_ph}) — becoming alkaline. Monitor nutrient uptake.")
            else:
                st.success(f"✅ pH {avg_ph} is optimal for {variety}.")

            if df_preview is not None and 'Soil_Moisture' in df_preview.columns:
                st.markdown("**📈 Moisture Trend**")
                st.line_chart(df_preview['Soil_Moisture'], use_container_width=True, color="#2E7D32")

            st.divider()
            alerts = result.get("alerts", [])
            report = f"""==========================================
AGRITEX MAIZE ADVISORY REPORT
==========================================
Date:     {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
Officer:  {current_user}
Location: {district} — {ward}
------------------------------------------
Variety:      {variety}
Field Status: {decision}
Avg Moisture: {avg_moisture}%
Avg pH:       {avg_ph}
------------------------------------------
AI RECOMMENDATIONS:
{'- Conditions optimal. Continue standard management.' if not alerts else chr(10).join(f'- {a}' for a in alerts)}
------------------------------------------
Generated by: Agritex Maize Intelligence AI
Zimbabwe Digital Support Unit © 2026
==========================================
"""
            st.download_button("📥 Download Advice Slip for Farmer",
                               data=report,
                               file_name=f"Advice_{ward}_{pd.Timestamp.now().strftime('%d%m%Y')}.txt",
                               mime="text/plain", use_container_width=True)
            st.info("💡 Share this report via WhatsApp or print for the farmer.")
        else:
            st.markdown("""
            <div style="text-align:center;padding:3rem 2rem;background:#FAFAFA;
                        border-radius:16px;border:2px dashed #E0E0E0;margin-top:0.5rem;">
                <div style="font-size:2.8rem;margin-bottom:0.6rem;">🌱</div>
                <div style="font-size:0.95rem;font-weight:600;color:#888;margin-bottom:0.3rem;">
                    No Analysis Yet
                </div>
                <div style="font-size:0.82rem;color:#bbb;">
                    Upload a CSV and click <strong>Run Smart Diagnostic</strong>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── REGIONAL TRENDS ──
    st.divider()
    st.markdown('<div class="section-title">📊 Live Regional Performance Trends</div>', unsafe_allow_html=True)

    @st.cache_data(ttl=30)
    def fetch_trends(d):
        try:
            r = requests.get(f"{BACKEND_URL}/get_trends", params={"district": d}, timeout=5)
            if r.status_code == 200:
                return r.json().get("data", [])
        except Exception:
            pass
        return []

    try:
        trends = fetch_trends(district)
        if trends:
            tdf = pd.DataFrame(trends).rename(columns={
                "ward": "Ward", "avg_moisture": "Moisture (%)",
                "avg_ph": "pH Level", "decision": "Last Decision"
            })
            tc, sc = st.columns([2.5, 1], gap="medium")
            with tc:
                st.dataframe(tdf, use_container_width=True, hide_index=True)
            with sc:
                if "Last Decision" in tdf.columns:
                    total = len(tdf)
                    crit  = len(tdf[tdf['Last Decision'] == 'Action Required'])
                    st.metric("Total Wards", total)
                    st.metric("Optimal Wards", total - crit)
                    if crit:
                        st.error(f"⚠️ {crit} ward{'s' if crit > 1 else ''} need attention")
                    else:
                        st.success("✅ All wards optimal")
        else:
            st.info(f"No trend data for **{district}** yet.")
    except Exception as e:
        st.warning(f"Could not load regional trends: {e}")

    # ── FOOTER ──
    st.markdown(f"""
    <div class="app-footer">
        <strong>Zimbabwe Agritex Digital Intelligence System</strong>
        &nbsp;·&nbsp; Active Officer: {current_user}
        &nbsp;·&nbsp; © 2026 &nbsp;·&nbsp; v7.0
    </div>""", unsafe_allow_html=True)