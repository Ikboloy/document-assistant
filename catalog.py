"""Server-side, opt-in catalog client for the single-user local lab."""
import http.client
import json
import os
import urllib.error
import urllib.request
from uuid import UUID

class CatalogError(Exception):
    pass

def configured():
    return bool(os.getenv("HASURA_ENDPOINT") and os.getenv("HASURA_GRAPHQL_ADMIN_SECRET"))

def execute(query, variables=None):
    if not configured():
        raise CatalogError("Catalog is not configured.")
    req = urllib.request.Request(
        os.environ["HASURA_ENDPOINT"],
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json",
                 "X-Hasura-Admin-Secret": os.environ["HASURA_GRAPHQL_ADMIN_SECRET"]})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.load(response)
        if result.get("errors") or not isinstance(result.get("data"), dict):
            raise CatalogError("Catalog request failed.")
        return result["data"]
    except (OSError, http.client.HTTPException, ValueError) as error:
        raise CatalogError("Catalog unavailable. Check local services and setup.") from None

def save_title(title, language, document_id):
    title = title.strip()
    if not 1 <= len(title) <= 200 or language not in ("en", "ko", "uz"):
        raise CatalogError("Use a title of 1–200 characters and a supported language.")
    document_id = str(UUID(document_id))
    return execute("""mutation($object: documents_insert_input!) {
      insert_documents_one(object: $object, on_conflict: {
        constraint: documents_pkey, update_columns: [title, language]
      }) { id title language created_at }
    }""", {"object": {"id": document_id, "title": title, "language": language}})["insert_documents_one"]

def list_titles():
    return execute("{ documents(limit: 100, order_by: [{created_at: desc}, {id: asc}]) { id title language created_at } }")["documents"]

def delete_title(document_id):
    return execute("mutation($id: uuid!) { delete_documents_by_pk(id: $id) { id } }",
                   {"id": str(UUID(document_id))})["delete_documents_by_pk"]
