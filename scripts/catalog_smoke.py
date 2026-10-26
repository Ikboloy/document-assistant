"""Exercise the same server-side client used by Streamlit against real Hasura."""
import os
from pathlib import Path
import sys
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import catalog

root = Path(__file__).resolve().parents[1]
env = dict(line.split("=", 1) for line in (root / ".env").read_text().splitlines() if "=" in line)
os.environ["HASURA_ENDPOINT"] = "http://127.0.0.1:8080/v1/graphql"
os.environ["HASURA_GRAPHQL_ADMIN_SECRET"] = env["HASURA_GRAPHQL_ADMIN_SECRET"]
uid = str(uuid4())
try:
    catalog.save_title('Integration " 한국어', "ko", uid)
    catalog.save_title("Updated title", "en", uid)
    rows = [r for r in catalog.list_titles() if r["id"] == uid]
    assert len(rows) == 1 and rows[0]["title"] == "Updated title", rows
finally:
    catalog.delete_title(uid)
assert not any(r["id"] == uid for r in catalog.list_titles())
print("PASS: application catalog client save/update/list/delete.")
