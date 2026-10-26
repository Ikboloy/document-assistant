"""Generate URL-safe development secrets without overwriting an existing .env."""
from pathlib import Path
import secrets

path = Path(__file__).resolve().parents[1] / ".env"
with path.open("x") as output:
    output.write("POSTGRES_PASSWORD=" + secrets.token_hex(24) + "\n")
    output.write("HASURA_GRAPHQL_ADMIN_SECRET=" + secrets.token_hex(32) + "\n")
path.chmod(0o600)
print("Created .env. Keep it private and retain it with your local database volume.")
