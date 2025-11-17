"""
type_scraper.py

Scraper orchestrator:
- Reuses BaseScraper
- Uses optional external Playwright context
- Loads cached HTML if exists
- Fetches single-page type chart
- Delegates parsing to type_chart_parser.parse_type_chart()
"""

from typing import Any, Optional, Dict

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from src.base import BaseScraper
from src.common.utils import save_html
from src.scrapers.types.parsers.type_chart_parser import parse_type_chart


class TypeScraper(BaseScraper):

    def __init__(
            self,
            url: str,
            file_name: str,
            scraper_settings: dict[str, Any],
            external_context=None
    ):
        super().__init__(url=url, file_name=file_name, scraper_settings=scraper_settings)
        self.external_context = external_context  # may reuse browser context

    # --------------------------------------------------------
    # Load cached HTML
    # --------------------------------------------------------
    def _load_cached_html(self) -> Optional[BeautifulSoup]:
        try:
            with open(self.raw_html_path, "r", encoding="utf-8") as f:
                html = f.read()
                print(f"[CACHE] Loaded cached HTML → {self.raw_html_path}")
                return BeautifulSoup(html, "lxml")
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"[CACHE ERROR] {e}")
            return None

    # --------------------------------------------------------
    # Playwright fetch (try external context → fallback)
    # --------------------------------------------------------
    def _fetch_html(self) -> Optional[BeautifulSoup]:

        # 1. Try cached
        cached = self._load_cached_html()
        if cached:
            return cached

        print(f"[Playwright] Fetching {self.url}")

        # 2. Try external shared context
        if self.external_context:
            try:
                page = self.external_context.new_page()
                page.goto(self.url, timeout=60000)
                page.wait_for_load_state("networkidle")

                html = page.content()
                save_html(html, self.raw_html_path)

                page.close()
                return BeautifulSoup(html, "lxml")
            except Exception as e:
                print(f"[Context fetch error] {e}")

        # 3. Full Playwright launch
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--no-sandbox",
                    ],
                )

                ctx = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 900},
                )
                ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")

                page = ctx.new_page()
                page.goto(self.url, timeout=60000)
                page.wait_for_load_state("networkidle")

                html = page.content()
                save_html(html, self.raw_html_path)

                page.close()
                ctx.close()
                browser.close()

                return BeautifulSoup(html, "lxml")

        except Exception as e:
            print(f"[FETCH ERROR] {e}")
            return None

    # --------------------------------------------------------
    # PARSE orchestrator
    # --------------------------------------------------------
    def parse(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Delegate to parser module
        """
        return parse_type_chart(soup)
