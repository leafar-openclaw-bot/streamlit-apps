"""
One-time migration: seeds Supabase `guests` table from guests.json.

Usage:
    pip install supabase
    SUPABASE_URL=https://xxx.supabase.co SUPABASE_KEY=eyJ... python seed_supabase.py

Or fill in the constants below directly (don't commit credentials).

Run this ONCE after creating the Supabase table with:

    CREATE TABLE guests (
        id       SERIAL PRIMARY KEY,
        name     TEXT UNIQUE NOT NULL,
        side     TEXT NOT NULL,
        groups   TEXT[] NOT NULL DEFAULT '{}',
        priority TEXT NOT NULL,
        notes    TEXT DEFAULT ''
    );
"""

import json, os, pathlib
from supabase import create_client

HERE = pathlib.Path(__file__).parent

def _read_secrets_toml():
    """Read url/key from .streamlit/secrets.toml if it exists."""
    toml_path = HERE / ".streamlit" / "secrets.toml"
    if not toml_path.exists():
        return None, None
    text = toml_path.read_text(encoding="utf-8")
    url = key = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("url") and "=" in line:
            url = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("key") and "=" in line:
            key = line.split("=", 1)[1].strip().strip('"')
    return url, key

_toml_url, _toml_key = _read_secrets_toml()
SUPABASE_URL = os.environ.get("SUPABASE_URL") or _toml_url or "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or _toml_key or "YOUR_ANON_KEY"

with open(HERE / "guests.json", encoding="utf-8") as f:
    guests = json.load(f)

# Normalize old schema just in case
for g in guests:
    if "groups" not in g:
        g["groups"] = [g.pop("group")] if "group" in g else []
    g.setdefault("notes", "")

# Strip any fields not in the DB schema
COLS = {"name", "side", "groups", "priority", "notes"}
rows = [{k: v for k, v in g.items() if k in COLS} for g in guests]

client = create_client(SUPABASE_URL, SUPABASE_KEY)
result = client.table("guests").upsert(rows, on_conflict="name").execute()
print(f"Seeded {len(result.data)} guests into Supabase.")
