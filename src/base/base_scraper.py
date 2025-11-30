import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup

from src.common import save_cache_html, load_cache_html

PIPELINE_TTL = {
    "hourly": 1 * 60 * 60,
    "daily": 12 * 60 * 60,
    "weekly": 3 * 24 * 60 * 60,
    "monthly": 30 * 24 * 60 * 60,
}

class BaseScraper(ABC):
    def __init__(self, scraper: Any, scraper_settings: dict[str, Any]):
        self.url = scraper["url"]
        self.file_name = scraper["file_name"]
        self.scraper_settings = scraper_settings

        root_dir = Path(__file__).resolve().parents[2]
        self.pipeline = scraper.get("pipeline", "daily")

        if scraper.get("subfolder") is None:
            subfolder = scraper.get("file_name")
        else:
            subfolder = scraper.get("subfolder", None)

        # --- Dynamic folder support ---
        html_dir = os.path.join(root_dir, "output", self.pipeline, "html")
        json_dir = os.path.join(root_dir, "output", self.pipeline, "json")

        if subfolder:
            html_dir = os.path.join(html_dir, subfolder)
            json_dir = os.path.join(json_dir, subfolder)

        # --- Final paths ---
        self.raw_html_path = os.path.join(html_dir, f"{self.file_name}.html")
        self.json_path = os.path.join(json_dir, f"{self.file_name}.json")

    def _fetch_html(self) -> Optional[BeautifulSoup]:
        retries = self.scraper_settings.get("retries", 3)
        delay = self.scraper_settings.get("delay", 5)
        timeout = self.scraper_settings.get("timeout", 15)

        for attempt in range(retries):
            print(f"Fetching HTML from {self.url} (Attempt {attempt + 1}/{retries})...", flush=True)
            try:
                response = requests.get(self.url, timeout=timeout)
                response.raise_for_status()

                save_cache_html(response.text, self.raw_html_path)

                return BeautifulSoup(response.content, "lxml")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching {self.url}: {e}", flush=True)
                if attempt < retries - 1:
                    print(f"Retrying in {delay} seconds...", flush=True)
                    time.sleep(delay)
                else:
                    print("All retry attempts failed.", flush=True)
                    return None
        return None

    def save_to_json(self, data: dict[Any, Any] | list[Any]):
        json_dir = os.path.dirname(self.json_path)
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)

        print(f"Saving data to {self.json_path}...")
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {self.json_path}")

    @abstractmethod
    def parse(self, soup: BeautifulSoup) -> dict[Any, Any] | list[Any]:
        pass

    def run(self):
        cached = load_cache_html(self.raw_html_path, PIPELINE_TTL[self.pipeline])
        if cached:
            soup = cached
        else:
            soup = self._fetch_html()
        if soup:
            data = self.parse(soup)
            self.save_to_json(data)
        else:
            self.save_to_json({})
