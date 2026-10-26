# Local PostgreSQL + Hasura lab

This is step 1 of the cloud learning track. Docker Compose runs the existing
Streamlit app, PostgreSQL 16 and Hasura GraphQL Engine v2.51.1.
The Streamlit upload flow is still in-memory: it does NOT yet save PDFs or
answers in PostgreSQL. The new catalog is exercised independently via GraphQL.

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
- App and database currently run independently; AI works through the existing
  optional provider flow. This is not yet a complete persistent RAG service.

## Your first exercise

1. Start the services and run the smoke test.
2. Insert an English and a Korean document title in the console.
3. Query only Korean titles with `documents(where: {language: {_eq: "ko"}})`.
4. Restart the stack and verify your two records remain.
5. Explain why a missing admin secret is rejected and why browser clients
   must never receive it.

## Next milestones

1. Connect app-side persistence with a clear opt-in and document deletion.
2. Add verified login and per-user Hasura permissions with isolation tests.
3. Add evaluated embeddings and source-backed answers.
4. Plan AWS S3/RDS/compute and budget before provisioning.
5. Add deployment through short-lived credentials, staged rollout and rollback.

References:
- https://hasura.io/docs/2.0/deployment/deployment-guides/docker/
- https://hasura.io/docs/2.0/api-reference/metadata-api/source/
- https://hasura.io/docs/2.0/schema/postgres/tables/
