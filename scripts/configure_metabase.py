"""Configures Metabase via its REST API: creates the admin account and
connects it to your existing Postgres. Safe to re-run.
"""
import json
import os
import urllib.request

from dotenv import load_dotenv

load_dotenv()
MB_URL = os.getenv("MB_URL", "http://localhost:3000")


def call(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Metabase-Session"] = token
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{MB_URL}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


props = call("GET", "/api/session/properties")

if props["has-user-setup"]:
    token = call("POST", "/api/session", {
        "username": os.getenv("MB_ADMIN_EMAIL"),
        "password": os.getenv("MB_ADMIN_PASSWORD"),
    })["id"]
else:
    token = call("POST", "/api/setup", {
        "token": props["setup-token"],
        "user": {
            "first_name": os.getenv("MB_ADMIN_FIRST_NAME"),
            "last_name": os.getenv("MB_ADMIN_LAST_NAME"),
            "email": os.getenv("MB_ADMIN_EMAIL"),
            "password": os.getenv("MB_ADMIN_PASSWORD"),
        },
        "prefs": {"site_name": os.getenv("MB_SITE_NAME", "Metabase")},
    })["id"]

db_name = os.getenv("PGDATABASE", "ghcnd_etl")
already_connected = any(
    db["name"] == db_name for db in call("GET", "/api/database", token=token)["data"]
)

if already_connected:
    print(f"Database '{db_name}' already connected, skipping.")
else:
    # host.docker.internal = Docker Desktop's DNS name for "the Mac this
    # container runs on" -- "localhost" here would mean the container itself.
    call("POST", "/api/database", {
        "engine": "postgres",
        "name": db_name,
        "details": {
            "host": "host.docker.internal",
            "port": int(os.getenv("PGPORT", 5432)),
            "dbname": db_name,
            "user": os.getenv("PGUSER"),
            "password": os.getenv("PGPASSWORD"),
        },
    }, token=token)
    print(f"Connected database '{db_name}'.")
