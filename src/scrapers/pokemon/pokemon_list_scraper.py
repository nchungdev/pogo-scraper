import random
import time
from typing import Any, List

import requests

from src.base.base_scraper import BaseScraper
from src.common import load_cache_json, save_cache_json
from src.scrapers.pokemon.pokemon_detail_scraper import PokemonDetailScraper

def _run_detail_pipeline(species_list: list[dict[str, Any]]):
    print(f"[PIPELINE] Total Pokémon to scrape: {len(species_list)}")

    for p in species_list:
        poke_id = p["id"]
        name = p["name"]
        url = p["detail_url"]

        scraper = PokemonDetailScraper(
            url=url,
            file_name=f"{poke_id:04d}-{name}",
            scraper_settings={"timeout": 60000}
        )

        print(f"→ Scraping #{poke_id:04d} {name}")
        scraper.run()

        time.sleep(random.uniform(0.3, 0.7))  # anti-block jitter

    print("=== Pokémon Pipeline Complete ===")


class PokemonListScraper(BaseScraper):

    def __init__(self, url: str, file_name: str, pipeline: str, scraper_settings: dict[str, Any], external_context=None):
        super().__init__(url, file_name, pipeline, scraper_settings=scraper_settings)
        self.external_context = external_context

    # ---------------------------------------------------
    # Completely override BaseScraper.run()
    # ---------------------------------------------------
    def run(self):
        print("=== Pokémon Species Scraper Started ===")

        species_list = self._load_or_fetch_species_list()

        print(f"[SPECIES] Total Pokémon to scrape: {len(species_list)}")

        # ---------------------------
        # Run Pokémon detail scraper
        # ---------------------------
        for p in species_list:
            poke_id = p["id"]
            name = p["name"]
            url = p["detail_url"]

            print(f"→ Scraping #{poke_id:04d} {name}")

            scraper = PokemonDetailScraper(
                url=url,
                file_name=f"{poke_id:04d}-{name}",
                scraper_settings={"timeout": 60000},
            )
            scraper.run()

            time.sleep(random.uniform(0.3, 0.7))

        print("=== Pokémon Species Scraper Complete ===")

    # ---------------------------------------------------
    # Fetch JSON or load cache
    # ---------------------------------------------------
    def _load_or_fetch_species_list(self) -> list[dict[str, Any]]:
        cached = load_cache_json(self.json_path)
        if cached:
            print("[CACHE] Loaded species list JSON")
            return self._normalize_results(cached.get("results", []))

        print("[FETCH] Fetching species list from PokeAPI...")
        resp = requests.get(self.url, timeout=30)
        resp.raise_for_status()

        api_data = resp.json()
        species_list = self._normalize_results(api_data.get("results", []))

        save_cache_json(api_data, self.json_path)

        return species_list

    # ---------------------------------------------------
    # Convert API "results" → normalized list
    # ---------------------------------------------------
    @staticmethod
    def _normalize_results(items: List[dict]) -> list[dict]:
        result = []

        for item in items:
            name = item["name"].strip().lower()
            url = item["url"]

            try:
                poke_id = int(url.rstrip("/").split("/")[-1])
                result.append({
                    "id": poke_id,
                    "name": name,
                    "detail_url": f"https://db.pokemongohub.net/pokemon/{poke_id}"
                })
            except:
                continue

        return sorted(result, key=lambda x: x["id"])

    # ---------------------------------------------------
    # This scraper does NOT parse HTML → disable parse()
    # ---------------------------------------------------
    def parse(self, soup):
        return []
