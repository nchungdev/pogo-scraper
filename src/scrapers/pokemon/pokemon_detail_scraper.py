"""
pokemon_detail_scraper.py

Main orchestrator class.
- Reuses BaseScraper
- Reuses external Playwright context if provided
- Loads cached HTML if exists
- Fetches page + expands form dropdown
- Parses sections via TOC and delegates to small parser modules
- Produces flat JSON: overview_and_stats contains header info + core stats
"""
from typing import Optional, Any, Dict

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from src.base.base_scraper import BaseScraper
from src.common.normalize import normalize_url
from src.common.utils import parse_toc, save_html
from src.scrapers.pokemon.parsers import *

BASE = "https://db.pokemongohub.net"


# ============================================================
#                     SCRAPER CLASS
# ============================================================
class PokemonDetailScraper(BaseScraper):

    def __init__(self, url: str, file_name: str, scraper_settings: dict[str, Any], external_context=None):
        super().__init__(url=url, file_name=file_name, scraper_settings=scraper_settings)
        self.external_context = external_context

    # ----------------------------------------
    # Cache loader
    # ----------------------------------------
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

    # ----------------------------------------
    # Playwright fetch (with fallback)
    # ----------------------------------------
    def _fetch_html(self) -> Optional[BeautifulSoup]:

        # ✓ 1. Try cache
        cached = self._load_cached_html()
        if cached:
            return cached

        print(f"[Playwright] Fetching {self.url}")

        # ✓ 2. Fast path: reuse external context
        if self.external_context:
            try:
                page = self.external_context.new_page()
                page.goto(self.url, timeout=60000)
                page.wait_for_selector(".CoreSelect_select__ABUYR[role='combobox']", timeout=15000)
                toggle = page.query_selector(".CoreSelect_select__ABUYR[role='combobox']")
                if toggle:
                    toggle.click()
                    page.wait_for_timeout(200)
                html = page.content()
                save_html(html, self.raw_html_path)
                page.close()
                return BeautifulSoup(html, "lxml")
            except Exception as e:
                print(f"[Context fetch error] {e}")

        # ✓ 3. Create new browser context (slow path)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ]
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

                # expand form dropdown
                try:
                    page.wait_for_selector(".CoreSelect_select__ABUYR[role='combobox']", timeout=15000)
                    t = page.query_selector(".CoreSelect_select__ABUYR[role='combobox']")
                    if t:
                        t.click()
                        page.wait_for_timeout(200)
                except:
                    pass

                html = page.content()
                save_html(html, self.raw_html_path)

                page.close()
                ctx.close()
                browser.close()

                return BeautifulSoup(html, "lxml")

        except Exception as e:
            print(f"[FETCH ERROR] {e}")
            return None

    # ============================================================
    #                            PARSE
    # ============================================================
    def parse(self, soup: BeautifulSoup) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        # --------------------------------------------------------
        # 1. HEADER (forms, artwork, types, weather, availability)
        # --------------------------------------------------------
        header = {
            "forms": parse_forms(soup, normalize_url),
            "official_artwork": parse_official_art(soup, normalize_url),
            "types": parse_types(soup),
            "weather_boost": parse_weather_boost(soup),
            "availability": parse_availability_flags(soup),
        }

        # --------------------------------------------------------
        # 2. TOC-driven sections
        # --------------------------------------------------------
        toc_ids = parse_toc(soup)

        for section_id in toc_ids:
            html_block = extract_section_html(soup, section_id)
            key = section_id.replace("-", "_")
            parser = (
                {
                    "overview_and_stats": parse_overview_stats,
                    "moves_and_best_movesets": parse_movesets,
                    "special_cp": parse_special_cp,
                    "max_cp_chart": parse_max_cp_chart,
                    "evolution_chart": parse_evolution,
                    "meta_analysis": parse_meta_analysis,
                    "mega_boost": parse_mega_boost,
                    "additional": parse_additional,
                    "pokedex": parse_pokedex_entries_table,
                    "sprites": parse_sprites,
                    "costumes": parse_costumes,
                    "faq": parse_faq,
                }
                .get(key)
            )

            if parser and html_block:
                try:
                    result[key] = parser(html_block)
                except Exception as e:
                    print(f"[WARN] parse failed for {key}: {e}")
                    result[key] = None

        # --------------------------------------------------------
        # 3. Merge HEADER into overview_and_stats
        # --------------------------------------------------------
        if "overview_and_stats" not in result or result["overview_and_stats"] is None:
            result["overview_and_stats"] = {}

        result["overview_and_stats"].update(header)

        return result
