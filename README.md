# Sheet Sync

Copies data from a Google Sheet ("Double Zone" tab) into a PostgreSQL table (`mg_output_double_zone`).

## Author
Leetesh - Junior IT

## How to run
1. Install the packages: `pip install pandas gspread sqlalchemy psycopg2-binary google-auth-oauthlib`
2. Put your Google `credentials_2.json` file in the right folder
3. Set your database password in the script
4. Run: `python3 sync_sheet_fast.py`



hello
