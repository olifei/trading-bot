import os
import firebase_admin
from firebase_admin import firestore
import json
from pathlib import Path
from dotenv import load_dotenv

# Single config source: trading_assistant/.env (loaded here so this module is
# self-sufficient regardless of which entry point imports it).
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

_db = None

def get_firestore_client():
    global _db
    if _db is not None:
        return _db

    # firebase_config.json is an optional fallback; .env is the primary source.
    config = {}
    config_path = Path(__file__).resolve().parent.parent.parent / "user_database/config/firebase_config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or config.get("project_id")
    database_id = os.environ.get("FIRESTORE_DATABASE_ID") or config.get("database_id")
    
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(options={
            'projectId': project_id,
        })
    
    _db = firestore.client(database_id=database_id)
    return _db
