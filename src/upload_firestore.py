# src/upload_firestore.py
import json
import os
import re
import sys
import time
from typing import Any, Dict, List

import firebase_admin
from firebase_admin import credentials, firestore

RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2


# ----------------------------------------------------------
# Repo root
# ----------------------------------------------------------
def get_repo_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))  # src/
    return os.path.abspath(os.path.join(script_dir, ".."))  # repo root


# ----------------------------------------------------------
# Config load
# ----------------------------------------------------------
def load_config(repo_root: str) -> Dict[str, Any]:
    config_path = os.path.join(repo_root, "src", "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------
# Firebase init
# ----------------------------------------------------------
def init_firebase(service_account_path: str):
    if not os.path.isfile(service_account_path):
        raise FileNotFoundError(f"Missing serviceAccount.json at: {service_account_path}")

    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    return firestore.client()


# ----------------------------------------------------------
# Find JSON files under output/<freq>/json/**
# ----------------------------------------------------------
def find_json_files(repo_root: str) -> List[str]:
    output_root = os.path.join(repo_root, "output")
    if not os.path.isdir(output_root):
        return []

    json_files = []

    for root, dirs, files in os.walk(output_root):
        path_parts = root.replace("\\", "/").split("/")
        if "json" not in path_parts:
            continue

        for fn in files:
            if fn.lower().endswith(".json"):
                json_files.append(os.path.join(root, fn))

    return sorted(json_files)


# ----------------------------------------------------------
# Resolve collection from config.json
# ----------------------------------------------------------


def resolve_collection(config: Dict[str, Any], filename: str) -> str:
    base = filename[:-5]  # remove .json

    # 1️⃣ Check explicit mapping in config.json
    for _, meta in config.get("scrapers", {}).items():
        if meta.get("file_name") == base:
            return meta.get("collection", "misc")

    # 2️⃣ Pokémon details: 4 digits + "-" + name
    #     e.g. 0001-bulbasaur, 0359-absol
    if re.match(r"^\d{4}-[a-z0-9_\-]+$", base):
        return "pokedex"

    # 3️⃣ Default fallback
    return "misc"


# ----------------------------------------------------------
# Firestore upload
# ----------------------------------------------------------
def upload_doc(db, collection: str, doc_id: str, data: Dict[str, Any]):
    payload = dict(data)
    payload["_updated_at"] = firestore.SERVER_TIMESTAMP

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            db.collection(collection).document(doc_id).set(payload)
            return
        except Exception as e:
            print(f"[WARN] Upload failed ({attempt}/{RETRY_ATTEMPTS}): {e}")

            if attempt == RETRY_ATTEMPTS:
                raise
            time.sleep(RETRY_BACKOFF ** attempt)


# ----------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------
def main():
    repo_root = get_repo_root()
    service_account_path = os.path.join(repo_root, "serviceAccount.json")

    print(f"[Firestore] repo_root = {repo_root}")

    config = load_config(repo_root)

    try:
        db = init_firebase(service_account_path)
    except Exception as e:
        print(f"[ERROR] Firebase init failed: {e}")
        sys.exit(1)

    files = find_json_files(repo_root)

    if not files:
        print("[Firestore] No JSON files found.")
        return

    print(f"[Firestore] Found {len(files)} JSON files.")

    any_error = False

    for path in files:
        filename = os.path.basename(path)
        base = filename[:-5]  # strip .json

        print(f"\n→ Processing JSON: {filename}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load {filename}: {e}")
            any_error = True
            continue

        collection = resolve_collection(config, filename)
        doc_id = base

        print(f"[Firestore] Upload → {collection}/{doc_id}")

        try:
            upload_doc(db, collection, doc_id, data)
        except Exception as e:
            print(f"[ERROR] Upload failed for {filename}: {e}")
            any_error = True
            continue

        print(f"[OK] Uploaded {collection}/{doc_id}")

    if any_error:
        sys.exit(2)

    print("\n[Firestore] All uploads complete.")


if __name__ == "__main__":
    main()