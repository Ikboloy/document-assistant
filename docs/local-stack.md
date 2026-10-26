# Local PostgreSQL + Hasura lab

This is step 1 of the cloud learning track. Docker Compose runs the existing
Streamlit app, PostgreSQL 16 and Hasura GraphQL Engine v2.51.1.
Streamlit now offers an opt-in title catalog via server-side Hasura requests.
Upload a readable PDF, expand Saved document titles, choose a title and tick the
save checkbox. Only title and selected UI language are saved. PDF bytes,
questions and answers remain in memory. Saved titles cannot reopen a PDF.
The catalog can be listed/deleted even without an uploaded PDF. Deletion requires
an explicit confirmation checkbox. Saving twice for the same upload session
updates the same row; re-uploading in a new session may create a new entry.

## Start (Windows, macOS, Linux)

Install Docker Desktop with Compose v2 and Python 3.12. Run from the repo root:

```sh
python scripts/init_local.py
docker compose up -d --build
python scripts/local_stack.py setup
python scripts/local_stack.py smoke
```

On macOS/Linux use python3 if python is unavailable.
Open http://localhost:8501 for the app and http://localhost:8080/console for Hasura.
Enter HASURA_GRAPHQL_ADMIN_SECRET from your local .env into the Hasura console.
Never put this secret into frontend code or commit .env.

In the console API explorer, run:

```graphql
mutation {
  insert_documents_one(object: {title: "My first document", language: "en"}) {
    id
    title
  }
}
query {
  documents(order_by: {created_at: desc}) {
    id
    title
    language
    created_at
  }
}
```

The smoke test inserts and deletes its own fixture, checks a read, verifies
database constraints and checks that requests without the admin secret fail.
Setup can be run twice; it preserves existing catalog rows. SQL files added
later require an explicit migration plan; editing a CREATE TABLE IF NOT EXISTS
statement will not upgrade an existing table.

## Operations and limits

- Only loopback ports are published. PostgreSQL has no host port.
- No anonymous role or user permissions are configured; this is an admin-only lab.
- PostgreSQL data and Hasura metadata persist in a named Docker volume.
- Stop with `docker compose down`; start again with `docker compose up -d`.
- Retain .env: changing its database password does not update existing volumes.
- `docker compose down -v` permanently deletes this lab database. Use only
  when intentionally discarding your own development data.
- Do not deploy this development configuration publicly. Authentication,
  per-user authorization, backups, TLS and limits remain future work.
- AWS resources and paid AI calls are not created by these commands.
- The server-side app uses the Hasura admin secret in this loopback-only,
  single-user lab. Do not expose the Streamlit port publicly: all sessions would
  share catalog access. User login and isolation are not implemented.
- AI uses the existing optional provider flow; PDF retrieval remains in memory.
- Run `python scripts/catalog_smoke.py` to test the actual application client.

## Your first exercise

1. Start the services and run the smoke test.
2. Insert an English and a Korean document title in the console.
3. Query only Korean titles with `documents(where: {language: {_eq: "ko"}})`.
4. Restart the stack and verify your two records remain.
5. Explain why a missing admin secret is rejected and why browser clients
   must never receive it.

## Next milestones

1. Extend the title catalog to opt-in PDF storage with a migration and retention plan.
2. Add verified login and per-user Hasura permissions with isolation tests.
3. Add evaluated embeddings and source-backed answers.
4. Plan AWS S3/RDS/compute and budget before provisioning.
5. Add deployment through short-lived credentials, staged rollout and rollback.

References:
- https://hasura.io/docs/2.0/deployment/deployment-guides/docker/
- https://hasura.io/docs/2.0/api-reference/metadata-api/source/
- https://hasura.io/docs/2.0/schema/postgres/tables/
