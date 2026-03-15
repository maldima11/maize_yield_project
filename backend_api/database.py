import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'maize_yield.db')

def init_db():
    """Create the tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS field_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            district TEXT,
            ward TEXT,
            variety TEXT,
            avg_moisture REAL,
            avg_ph REAL,
            decision TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_report(district, ward, variety, moisture, ph, decision):
    """Save a new report to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO field_reports (district, ward, variety, avg_moisture, avg_ph, decision)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (district, ward, variety, moisture, ph, decision))
    conn.commit()
    conn.close()

def get_regional_summary(district):
    """Fetch the latest status of all wards in a district."""
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT ward, AVG(avg_moisture) as moisture, AVG(avg_ph) as ph, decision FROM field_reports WHERE district = '{district}' GROUP BY ward"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df