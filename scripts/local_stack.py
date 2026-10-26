"""Apply the local schema and track it in Hasura; smoke-test CRUD and auth."""
import json
import http.client
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8080"
secret = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines() if "=" in line)["HASURA_GRAPHQL_ADMIN_SECRET"]

def request(path, payload=None, auth=True):
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["X-Hasura-Admin-Secret"] = secret
    body = None if payload is None else json.dumps(payload).encode()
    with urllib.request.urlopen(urllib.request.Request(URL + path, data=body, headers=headers), timeout=10) as response:
        raw = response.read()
        return json.loads(raw) if payload is not None else raw

def graphql(query, variables=None):
    result = request("/v1/graphql", {"query": query, "variables": variables or {}})
    if "errors" in result:
        raise RuntimeError(result["errors"])
    return result["data"]

def setup():
    for attempt in range(60):
        try:
            request("/healthz")
            break
        except (OSError, http.client.HTTPException):
            if attempt == 59:
                raise
            time.sleep(2)
    request("/v1/metadata", {"type": "pg_add_source", "args": {
        "name": "default", "kind": "postgres", "replace_configuration": True,
        "configuration": {"connection_info": {"database_url": {"from_env": "PG_DATABASE_URL"}}}}})
    request("/v2/query", {"type": "run_sql", "args": {
        "source": "default", "sql": (ROOT / "infra/001_documents.sql").read_text()}})
    metadata = request("/v1/metadata", {"type": "export_metadata", "args": {}})
    source = next(s for s in metadata["sources"] if s["name"] == "default")
    if not any(t["table"] == {"schema": "public", "name": "documents"} for t in source["tables"]):
        request("/v1/metadata", {"type": "pg_track_table", "args": {
            "source": "default", "table": {"schema": "public", "name": "documents"}}})
    print("Schema applied; documents tracked. No anonymous/user permissions enabled.")

def smoke():
    try:
        result = request("/v1/graphql", {"query": "{ documents { id } }"}, auth=False)
    except urllib.error.HTTPError as error:
        if error.code not in (400, 401, 403):
            raise
    else:
        if not result.get("errors") or result.get("data"):
            raise AssertionError("Unauthenticated access was not rejected")
    item = graphql('mutation { insert_documents_one(object: {title: "CI smoke fixture", language: "en"}) { id } }')["insert_documents_one"]
    variables = {"id": item["id"]}
    try:
        row = graphql("query($id: uuid!) { documents_by_pk(id: $id) { title language } }", variables)["documents_by_pk"]
        assert row == {"title": "CI smoke fixture", "language": "en"}, row
        try:
            graphql('mutation { insert_documents_one(object: {title: "", language: "invalid"}) { id } }')
        except RuntimeError:
            pass
        else:
            raise AssertionError("Invalid document accepted")
    finally:
        graphql("mutation($id: uuid!) { delete_documents_by_pk(id: $id) { id } }", variables)
    assert graphql("query($id: uuid!) { documents_by_pk(id: $id) { id } }", variables)["documents_by_pk"] is None
    print("PASS: insert/read/delete, SQL constraints, unauthenticated rejection.")

if __name__ == "__main__":
    {"setup": setup, "smoke": smoke}[sys.argv[1]]()
