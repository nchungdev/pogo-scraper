import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup

from src.common import save_cache_html, load_cache_html


class BaseScraper(ABC):
    def __init__(
            self,
            url: str,
            file_name: str,
            pipeline: str,
            scraper_settings: dict[str, Any],
            subfolder: str = None,          # <— NEW
    ):
        # Resolve project root
        root_dir = Path(__file__).resolve().parents[2]
        self.url = url
        self.scraper_settings = scraper_settings
        self.pipeline = pipeline

        # --- Dynamic folder support ---
        html_dir = os.path.join(root_dir, "output", pipeline, "html")
        json_dir = os.path.join(root_dir, "output", pipeline, "json")

        if subfolder:
            html_dir = os.path.join(html_dir, subfolder)
            json_dir = os.path.join(json_dir, subfolder)

        # --- Final paths ---
        self.raw_html_path = os.path.join(html_dir, f"{file_name}.html")
        self.json_path = os.path.join(json_dir, f"{file_name}.json")

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
        cached = load_cache_html(self.raw_html_path)
        if cached:
            soup = cached
        else:
            soup = self._fetch_html()
        if soup:
            data = self.parse(soup)
            self.save_to_json(data)
        else:
            self.save_to_json({})
