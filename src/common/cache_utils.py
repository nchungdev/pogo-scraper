import json
import os
import time
from typing import Any, Optional

from bs4 import BeautifulSoup


# -----------------------------
# Internal helpers
# -----------------------------
def _meta_path(path: str) -> str:
    return f"{path}.metadata"


def _is_cache_valid(path: str, max_age: int) -> bool:
    meta_path = _meta_path(path)

    if not os.path.exists(path) or not os.path.exists(meta_path):
        return False

    try:
        with open(meta_path, "r", encoding="utf-8") as mf:
            meta = json.load(mf)

        age = time.time() - meta.get("created_time", 0)
        return age <= max_age

    except:
        return False


def _write_meta(path: str):
    meta_file = _meta_path(path)
    meta_data = {"created_time": int(time.time())}

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=4)


# -----------------------------
# HTML CACHE
# -----------------------------
def save_cache_html(html: str, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    _write_meta(path)
    print(f"[CACHE] Saved HTML → {path}")


def load_cache_html(path: str, max_age: int = 86400) -> Optional[BeautifulSoup]:
    """
    Return BeautifulSoup if cache valid, else None.
    """
    if not _is_cache_valid(path, max_age):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()

        age = int(time.time() - json.load(open(_meta_path(path)))["created_time"])
        print(f"[CACHE] Loaded HTML → {path} (age={age}s)")

        return BeautifulSoup(html, "lxml")
    except Exception as e:
        print(f"[CACHE ERROR] {e}")
        return None


# -----------------------------
# JSON CACHE
# -----------------------------
def save_cache_json(data: Any, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    _write_meta(path)
    print(f"[CACHE] Saved JSON → {path}")


def load_cache_json(path: str, max_age: int = 86400) -> Optional[Any]:
    """
    Load JSON only if:
      - file exists
      - metadata exists
      - cache not expired
    """
    if not _is_cache_valid(path, max_age):
        return None

    meta_path = _meta_path(path)

    try:
        # Load JSON content
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Load metadata
        with open(meta_path, "r", encoding="utf-8") as mf:
            meta = json.load(mf)

        age = int(time.time() - meta.get("created_time", 0))
        print(f"[CACHE] Loaded JSON → {path} (age={age}s)")

        return data

    except Exception as e:
        print(f"[CACHE ERROR] Failed loading: {e}")
        return None
