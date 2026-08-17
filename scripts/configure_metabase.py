"""Configures Metabase via its REST API: creates the admin account and
connects it to Postgres. Safe to re-run.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()
MB = os.getenv("MB_URL", "http://localhost:3000")
db_name = os.getenv("PGDATABASE", "ghcnd_etl")

props = requests.get(f"{MB}/api/session/properties").json()

if props["has-user-setup"]:
    token = requests.post(f"{MB}/api/session", json={
        "username": os.getenv("MB_ADMIN_EMAIL"),
        "password": os.getenv("MB_ADMIN_PASSWORD"),
    }).json()["id"]
else:
    token = requests.post(f"{MB}/api/setup", json={
        "token": props["setup-token"],
        "user": {
            "first_name": os.getenv("MB_ADMIN_FIRST_NAME"),
            "last_name": os.getenv("MB_ADMIN_LAST_NAME"),
            "email": os.getenv("MB_ADMIN_EMAIL"),
            "password": os.getenv("MB_ADMIN_PASSWORD"),
        },
        "prefs": {"site_name": os.getenv("MB_SITE_NAME", "Metabase")},
    }).json()["id"]

headers = {"X-Metabase-Session": token}
already_connected = any(
    db["name"] == db_name for db in requests.get(f"{MB}/api/database", headers=headers).json()["data"]
)

if already_connected:
    print(f"Database '{db_name}' already connected, skipping.")
else:
    # "postgres" = the Compose service name -- Metabase and Postgres share
    # the same Docker network, so they reach each other by service name.
    requests.post(f"{MB}/api/database", headers=headers, json={
        "engine": "postgres",
        "name": db_name,
        "details": {
            "host": "postgres",
            "port": int(os.getenv("PGPORT", 5432)),
            "dbname": db_name,
            "user": os.getenv("PGUSER"),
            "password": os.getenv("PGPASSWORD"),
        },
    })
    print(f"Connected database '{db_name}'.")
