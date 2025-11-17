# scrape_all_pokemon_sync.py

import json
import os
import random
import time

import requests

from src.scrapers import PokemonDetailScraper

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = os.path.join(PROJECT_ROOT, "src", "json")
CACHE_FILE = os.path.join(JSON_DIR, "pokemon_species_cache.json")
BASE_URL = "https://db.pokemongohub.net/pokemon/"
POKEAPI_URL = "https://pokeapi.co/api/v2/pokemon-species?limit=100000"


# ---------------------------------------------------
# LOAD OR FETCH SPECIES CACHE
# ---------------------------------------------------
def load_or_fetch_species_cache():
    """
    If pokemon_species_cache.json exists → load.
    If not → fetch from PokeAPI and generate {name: id}.
    """
    # Case 1: file cache đã tồn tại
    if os.path.exists(CACHE_FILE):
        print(f"[OK] Loaded species cache → {CACHE_FILE}")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # Case 2: cache chưa có → fetch API
    print("[INFO] species cache NOT FOUND → fetching from PokeAPI...")
    resp = requests.get(POKEAPI_URL, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    results = data.get("results", [])

    species_map = {}

    for item in results:
        name = item["name"].strip().lower()
        url = item["url"]

        # url dạng:
        #   https://pokeapi.co/api/v2/pokemon-species/1/
        try:
            poke_id = int(url.rstrip("/").split("/")[-1])
            species_map[name] = poke_id
        except:
            continue

    # Tạo thư mục json nếu chưa có
    os.makedirs(JSON_DIR, exist_ok=True)

    # Save lại
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(species_map, f, ensure_ascii=False, indent=4)

    print(f"[SAVED] species cache created → {CACHE_FILE}")
    return species_map


# ---------------------------------------------------
# SCRAPE 1 POKÉMON
# ---------------------------------------------------
def scrape_one(name: str, poke_id: int):
    url = f"{BASE_URL}{poke_id}"
    file_name = f"{poke_id:04d}-{name}"

    scraper = PokemonDetailScraper(
        url=url,
        file_name=file_name,
        scraper_settings={
            "timeout": 60_000
        }
    )

    print(f"===> Scraping {poke_id} - {name} ...")
    scraper.run()
    print(f"✓ Done {poke_id} - {name}")


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
def main():
    # 1️⃣ Luôn gọi load_or_fetch
    species = load_or_fetch_species_cache()

    # 2️⃣ Bắt đầu scrape
    count = 0

    for name, poke_id in species.items():
        scrape_one(name, poke_id)

        # Slight jitter to avoid CF bot checks
        time.sleep(random.uniform(0.3, 0.8))

        count += 1

        # anti-block cooldown
        if count % 80 == 0:
            print("Cooling down 10s to avoid CF blocking…")
            time.sleep(10)


if __name__ == "__main__":
    main()
