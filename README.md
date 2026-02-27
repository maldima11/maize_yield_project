# maize_yield_project
A Hybrid AI framework for predicting maize yields in data-scarce environments using Generative AI, Transfer Learning, and multi-channel dissemination (USSD, Mobile, Web) for smallholder farmers in Zimbabwe.

Phase 7: Inclusive Dissemination and Designed Interaction Architecture
This phase focuses on the "last mile" delivery of the AI model's insights. Because smallholder farmers in Sub-Saharan Africa experience varying levels of digital literacy and internet access, this framework deploys predictions across multiple inclusive channels: a Web Dashboard, a Zero-Data USSD/SMS system, Voice AI (IVR), and an offline-capable Mobile App.

📂 Folder Structure
To prevent dependency conflicts between the Python AI backend and the Dart/Flutter frontend, the repository is structured as follows:

maize_yield_project/
│
├── backend_api/                 # Python Flask Server (AI Engine, Mock API, & USSD Logic)
│   ├── venv/                    # Python virtual environment
│   ├── app.py                   # Main Flask application and API routes
│   ├── ussd_handler.py          # Africa's Talking USSD/SMS logic
│   └── requirements.txt         # Dependencies (Flask, requests, tensorflow, etc.)
│
├── web_dashboard/               # Interactive Web Interface
│   ├── app.py                   # Main dashboard application (Streamlit)
│   └── requirements.txt         # Dependencies specific to the web UI
│
├── mobile_app/                  # Flutter Application (for Extension Officers)
│   ├── lib/
│   │   ├── main.dart            # Flutter app entry point
│   │   ├── services/            # API connection logic
│   │   └── database/            # SQLite local caching logic
│   └── pubspec.yaml             # Flutter dependencies
│
└── notebooks/                   # Jupyter/Colab Notebooks for Model Training
├── 01_data_extraction.ipynb
└── 02_model_training.ipynb

🛠️ Prerequisites & Local Setup (macOS)
To run these interfaces locally on your Mac, ensure you have the following installed:

VS Code: Primary IDE.

Python 3.x: For the Flask backend and Streamlit dashboard.

Flutter SDK & Xcode: To build and simulate the iOS/Android mobile application.

Ngrok: To securely expose your local Mac server to the internet for the Africa's Talking USSD simulator to access.

Postman: For testing API endpoints.

🚀 Step-by-Step Implementation Guide
1. The Core Backend API (Flask)
The Flask backend serves as the central brain, hosting the AI predictive engine and routing requests to the various front-end channels.

Navigate to the backend directory: cd backend_api

Activate the virtual environment and install dependencies: pip install -r requirements.txt

Run the Flask server: python app.py (Runs locally on http://127.0.0.1:5000).

Expose to the Internet: In a new terminal, run ngrok http 5000. Copy the generated https:// URL.

2. Zero-Data USSD & SMS System (Africa's Talking)
This system allows farmers with basic feature phones to access yield predictions and agronomic advice without internet data.

Create a free Sandbox account on(https://africastalking.com/).

Navigate to USSD -> Create Channel and register a shortcode (e.g., *3664#).

Paste your Ngrok URL into the Callback URL field. This routes the telecom gateway requests to your local Flask app.

The logic in ussd_handler.py processes the HTTP POST requests. Menus begin with CON (Continue session) and terminate with END (End session and deliver prediction).

3. Voice AI / Interactive Voice Response (IVR)
Designed for illiterate farmers or those who struggle with text-based menus, this translates spoken queries into actionable advice.

In the Africa's Talking Sandbox, navigate to Voice and create a virtual phone number.

The Flask API handles incoming calls using XML-like responses to <Play>, <Say>, or <GetDigits>.

The system integrates Automatic Speech Recognition (ASR) to translate spoken Shona/Ndebele into text, processes the query against the AI model, and uses Text-to-Speech (TTS) to deliver the spoken agronomic recommendation.

4. Interactive Web Dashboard (Streamlit)
A high-level interface for Agritex extension officers and policymakers to view regional data and perform batch yield predictions.

Navigate to the dashboard directory: cd web_dashboard

Install requirements: pip install -r requirements.txt

Run the application: streamlit run app.py

The dashboard will automatically open in your browser, utilizing requests.get() to pull live data and predictions from your local Flask API.

5. Lightweight Mobile App (Flutter)
A cross-platform tool for agricultural extension workers operating in deep rural areas.

Navigate to the app directory: cd mobile_app

Run the app on a local iOS/Android simulator: flutter run

Offline-First Architecture: The app utilizes sqflite (SQLite for Flutter) to cache farmer inputs (GPS coordinates, planting dates) locally when cellular service is unavailable.

Background Sync: Once the device reconnects to Wi-Fi, the app automatically pushes the cached SQLite data to the Flask API to generate updated yield forecasts.