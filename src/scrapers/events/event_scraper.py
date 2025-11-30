# src/scrapers/event_scraper.py
import json
import logging
import os
import time
from typing import Any, Optional, cast

import requests
from bs4 import BeautifulSoup, Tag

from .event_page_scraper import EventPageScraper, jitter
from ...base import BaseScraper
from ...common.utils import clean_banner_url

logger = logging.getLogger(__name__)


def scrape_single_event_page(url: str, scraper: EventPageScraper) -> Optional[dict[str, Any]]:
    return scraper.scrape(url)

def convert_events_json(old_json: dict) -> dict:
    result = []

    for category, events in old_json.items():
        for event in events:
            flat = {
                "category": category,
                "title": event.get("title"),
                "article_url": event.get("article_url"),
                "banner_url": event.get("banner_url") or event.get("banner"),
                "is_local_time": event.get("is_local_time"),
                "start_time": event.get("start_time"),
                "end_time": event.get("end_time"),
                "description": event.get("description"),
                "details": event.get("details", {}),
            }
            result.append(flat)
    return {"results": result}

class EventScraper(BaseScraper):
    def __init__(
            self,
            scraper: Any,
            scraper_settings: dict[str, Any],
            check_existing_events: bool = False,
            github_user: Optional[str] = None,
            github_repo: Optional[str] = None,
    ):
        super().__init__(scraper, scraper_settings)
        self.check_existing_events = check_existing_events
        self.github_user = github_user
        self.github_repo = github_repo
        self.existing_event_urls: set[str] = set()
        self.existing_events_data: dict[str, list[dict[str, Any]]] = {}
        if self.check_existing_events:
            self._fetch_existing_events()

        # prepare html dir for saved pages + progress
        base_html_dir = os.path.dirname(getattr(self, "raw_html_path", "") or "")
        if not base_html_dir:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            base_html_dir = os.path.join(project_root, "src", "html")
        self.html_dir = os.path.join(base_html_dir, f"{self.file_name}_pages")
        os.makedirs(self.html_dir, exist_ok=True)
        self.progress_file = os.path.join(self.html_dir, "progress.json")

    def _fetch_existing_events(self):
        if not self.github_user or not self.github_repo:
            print(
                "GitHub user or repo not configured. Skipping check for existing events.",
                flush=True
            )
            return

        data_url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/data/events.json"
        try:
            timeout = self.scraper_settings.get("timeout", 15)
            response = requests.get(data_url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            self.existing_events_data = data
            for category in data.values():
                for event in category:
                    self.existing_event_urls.add(event["article_url"])
            print(f"Found {len(self.existing_event_urls)} existing events.", flush=True)
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Could not fetch existing events: {e}", flush=True)
            self.existing_events_data = {}

    def _load_progress(self) -> dict:
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"last_index": 0, "total": 0}

    def _save_progress(self, last_index: int, total: int):
        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump({"last_index": last_index, "total": total}, f, indent=2)
        except Exception as e:
            logger.warning(f"[EventScraper] Could not write progress file: {e}")

    def parse(self, soup: BeautifulSoup) -> dict[str, list[dict[str, Any]]]:
        """
        Parse index page soup into event list (same selectors as original).
        This method preserves original behavior: returns merged events structure.
        """
        events_to_scrape: list[dict[str, Any]] = []
        event_links = soup.select("a.event-item-link")
        print(f"Found {len(event_links)} event links", flush=True)

        for link in event_links:
            link = cast(Tag, link)
            href = link.get("href")
            if not href:
                continue

            title_element = link.select_one("div.event-text h2")
            if not title_element:
                continue

            image_element = link.select_one(".event-img-wrapper img")
            category_element = link.select_one(".event-item-wrapper > p")

            article_url = "https://leekduck.com" + str(href)

            if self.check_existing_events and article_url in self.existing_event_urls:
                continue

            banner_url = None
            if image_element and image_element.has_attr("src"):
                banner_url = clean_banner_url(str(image_element["src"]).strip())

            events_to_scrape.append({
                "title": title_element.get_text(strip=True),
                "article_url": article_url,
                "banner_url": banner_url,
                "category": category_element.get_text(strip=True) if category_element else "Event",
            })

        # build dict keyed by article_url
        all_events_data = {e["article_url"]: e for e in events_to_scrape}

        # fetch details using Playwright EventPageScraper
        if events_to_scrape:
            print(f"Initializing Playwright EventPageScraper for {len(events_to_scrape)} events...", flush=True)
            page_scraper = EventPageScraper(self.scraper_settings)
            try:
                total = len(events_to_scrape)
                progress = self._load_progress()
                last = int(progress.get("last_index", 0))
                # iterate with resume support
                for idx, ev in enumerate(events_to_scrape, start=1):
                    url = ev["article_url"]
                    if idx <= last:
                        # attempt to read saved html and parse it to keep results consistent
                        slug = url.rstrip("/").split("/")[-1]
                        saved = os.path.join(self.html_dir, f"{slug}.html")
                        if os.path.exists(saved):
                            with open(saved, "r", encoding="utf-8") as f:
                                html = f.read()
                                parsed = page_scraper._parse_html(html, url)
                                if parsed:
                                    all_events_data[url].update(parsed)
                        continue

                    print(f"Processing event {idx}/{total}: {ev['title']}", flush=True)
                    try:
                        parsed = scrape_single_event_page(url, page_scraper)
                        if parsed:
                            all_events_data[url].update(parsed)
                            # save raw html already handled inside page scraper fetch (if you want)
                            slug = url.rstrip("/").split("/")[-1]
                            saved = os.path.join(self.html_dir, f"{slug}.html")
                            # ensure saved exists (page scraper saved it); if not, create from parsed html if available
                        else:
                            logger.warning(f"[EventScraper] No parsed data for {url}")
                    except Exception as e:
                        logger.exception(f"[EventScraper] Error scraping detail {url}: {e}")

                    # progress & polite sleep
                    self._save_progress(idx, total)
                    time.sleep(jitter(1.0, 0.6))

            finally:
                try:
                    page_scraper.close()
                except Exception:
                    pass

        # group by category
        new_events_by_category: dict[str, list[dict[str, Any]]] = {}
        for ev in all_events_data.values():
            cat = ev.get("category", "Event")
            new_events_by_category.setdefault(cat, []).append(ev)

        # merge with existing events
        merged = self.existing_events_data.copy()
        for cat, evs in new_events_by_category.items():
            merged.setdefault(cat, []).extend(evs)

        # convert to old flat results format if needed
        return convert_events_json(merged)
