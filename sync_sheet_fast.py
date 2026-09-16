import io
import os
import time
import pickle
import pandas as pd
import gspread
from sqlalchemy import create_engine
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from gspread.exceptions import APIError

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_gspread_client():
    creds = None
    pickle_path = '/Users/Leetesh/Documents/MasterCogsDB-v2/token.pickle'
    
    if os.path.exists(pickle_path):
        with open(pickle_path, 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/Users/Leetesh/Documents/MasterCogsDB-v2/credentials_2.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
            
        with open(pickle_path, 'wb') as token:
            pickle.dump(creds, token)
            
    return gspread.authorize(creds)

def fetch_values_with_retry(worksheet, retries=5):
    """Fetches data safely to prevent 503 timeouts on large sheets."""
    for attempt in range(retries):
        try:
            print("Fetching sheet data from Google...")
            return worksheet.get_all_values()
        except APIError as e:
            if "503" in str(e) and attempt < retries - 1:
                wait_time = (attempt + 1) * 3
                print(f"Google server busy (503). Retrying in {wait_time}s... (Attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
            else:
                raise e

# 1. Connect
gc = get_gspread_client()
sh = gc.open_by_key('1WL0ZM-60nLXtmxVrOOGWaTyn7YPHkkKqMcqAP1CE-zY')
worksheet = sh.worksheet("Double Zone")

# 2. Fetch data safely
data = fetch_values_with_retry(worksheet)
headers = data[0]
rows = data[1:]

df = pd.DataFrame(rows, columns=headers)

# 3. Connect to PostgreSQL (Ensure password & DB match your setup)
engine = create_engine('postgresql://postgres:YOUR_PASSWORD@localhost:5432/YOUR_DB')

def postgres_copy_stream(table_name, engine, df, chunksize=2000):
    connection = engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")
        
        for i in range(0, len(df), chunksize):
            chunk = df.iloc[i:i + chunksize]
            s_buf = io.StringIO()
            chunk.to_csv(s_buf, index=False, header=False)
            s_buf.seek(0)
            cursor.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV", s_buf)
            
        connection.commit()
        print(f"Successfully streamed {len(df)} rows into {table_name}!")
    finally:
        connection.close()

# Execute sync
postgres_copy_stream('mg_output_double_zone', engine, df)