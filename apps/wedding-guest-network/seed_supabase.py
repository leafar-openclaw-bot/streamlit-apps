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

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://YOUR_PROJECT_ID.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_ANON_KEY")

HERE = pathlib.Path(__file__).parent
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
