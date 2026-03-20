"""
One-off: fix REG-030 next_date from 2026-11 to 30/11/2026 in the Events sheet.
"""
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1Tvg30ZkRbomed3zVIx42DLcAAYVK9q50m4yX-hJwu68"
KEY_PATH = Path(__file__).parent / "CB_market-stats-key.json"

creds = Credentials.from_service_account_file(str(KEY_PATH), scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
])
ws = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Events")

data = ws.get_all_values()
headers = data[0]
next_date_col = headers.index("next_date") + 1  # 1-indexed

for i, row in enumerate(data[1:], start=2):
    if row[0] == "REG-030":
        ws.update_cell(i, next_date_col, "30/11/2026")
        print(f"Updated REG-030 next_date → 30/11/2026 (row {i})")
        break
