import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# 1. Configure the page
st.set_page_config(page_title="Maize Yield Dashboard", layout="wide")
st.title("🌾 Umzingwane Maize Yield Prediction Dashboard")
st.markdown("Interactive AI dashboard for Agritex extension officers and policymakers.")

# 2. Sidebar for Administrative Filters
st.sidebar.header("Administrative Filters")
ward = st.sidebar.selectbox("Select Ward", ["Ward 1", "Ward 2", "Ward 3", "Ward 4", "Ward 5"])  # Fix 1: Added options list
variety = st.sidebar.selectbox("Select Maize Variety", ["SC 301", "SC 529", "ZM 521", "ZM 309"])  # Fix 1: Added options list

# 3. Live Prediction Section (Connecting to your Flask API)
st.header(f"Live Yield Forecast: {ward}")
st.write(f"Generate an instant forecast for the {variety} variety based on current regional conditions.")

if st.button("Generate Forecast"):
    try:
        # Call your local Flask Mock API
        response = requests.post(
            "http://127.0.0.1:5000/predict_yield",
            json={"variety": variety}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            col1.metric("Predicted Yield", f"{data['predicted_yield_kg_ha']} kg/ha")
            col2.metric("Selected Variety", data['variety'])
            col3.metric("System Status", "Optimal")
            
            # Display actionable AI feedback
            st.info(f"**Agronomic Recommendation:** {data['recommendation']}")
            st.warning(f"**Weather Alert:** {data['weather_alert']}")
        else:
            st.error("Error: Failed to fetch data from the API.")
            
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Is your Flask backend running on port 5000?")

st.divider()

# 4. Batch Prediction & Visualization Section
st.header("📂 Batch Data Upload & Analysis")
st.write("Upload historical CSV datasets to visualize regional trends.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    # Read the uploaded CSV
    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head())
    
    # Check if the CSV has the right columns to draw a chart
    if 'Date' in df.columns and 'Yield' in df.columns:
        st.subheader("Yield Trend Analysis")
        # Ensure Date is recognized correctly
        df['Date'] = pd.to_datetime(df['Date'])  # Fix 2: Must specify the column, not the whole DataFrame
        chart_data = df.set_index('Date')[['Yield']]  # Fix 3: Select only the Yield column for the chart
        
        # Draw an interactive line chart
        st.line_chart(chart_data)
    else:
        st.write("Upload a CSV containing 'Date' and 'Yield' columns to automatically generate trend charts.")