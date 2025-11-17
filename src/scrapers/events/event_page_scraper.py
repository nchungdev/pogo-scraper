# src/scrapers/event_page_scraper.py
import logging
import random
import time
from typing import Any, Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from src.common.utils import clean_banner_url

logger = logging.getLogger(__name__)

# lightweight pools (override via settings if needed)
DEFAULT_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

DEFAULT_VIEWPORT_POOL = [
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1600, "height": 900},
    {"width": 1920, "height": 1080},
]


def jitter(base: float = 1.0, var: float = 0.6) -> float:
    return base + random.random() * var


def backoff_delay(attempt: int, base: float = 1.0) -> float:
    return base * (1.6 ** (attempt - 1)) + random.random() * 0.5


class EventPageScraper:
    """
    Playwright-based scraper for a single event detail page.
    Public API:
      - scrape(url) -> dict | None
      - close() -> closes any persistent browser resources (no-op here)
    """

    def __init__(self, scraper_settings: dict[str, Any] | None = None):
        scraper_settings = scraper_settings or {}
        self.headless = scraper_settings.get("headless", True)
        self.pw_timeout = int(scraper_settings.get("pw_timeout", 60000))
        self.retries = int(scraper_settings.get("retries", 3))
        self.wait_after_idle = float(scraper_settings.get("wait_after_idle", 0.8))
        self.ua_pool = scraper_settings.get("ua_pool", DEFAULT_UA_POOL)
        self.viewport_pool = scraper_settings.get("viewport_pool", DEFAULT_VIEWPORT_POOL)
        self.stealth = bool(scraper_settings.get("stealth", True))
        self.backoff_base = float(scraper_settings.get("backoff_base", 1.0))
        # we do not keep a long-living browser here (creating/closing per request),
        # because that matches the previous Selenium per-page approach and avoids reuse issues.

    def _random_user_agent(self) -> str:
        return random.choice(self.ua_pool)

    def _random_viewport(self) -> dict:
        return random.choice(self.viewport_pool)

    def _humanize_page(self, page):
        # small random mouse moves and scrolls
        try:
            for _ in range(random.randint(1, 3)):
                x = random.randint(10, 1000)
                y = random.randint(10, 800)
                steps = random.randint(8, 25)
                try:
                    page.mouse.move(x, y, steps=steps)
                except Exception:
                    pass
                time.sleep(random.random() * 0.12)
            for _ in range(random.randint(1, 2)):
                try:
                    page.evaluate("window.scrollBy(0, window.innerHeight/3)")
                except Exception:
                    pass
                time.sleep(random.random() * 0.18)
        except Exception:
            pass

    def _fetch_html_with_playwright(self, url: str, attempt_limit: int = 3) -> Optional[str]:
        for attempt in range(1, attempt_limit + 1):
            ua = self._random_user_agent()
            vp = self._random_viewport()
            logger.info(f"[EventPageScraper] Fetch attempt {attempt} url={url}")

            try:
                with sync_playwright() as p:
                    launch_args = [
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--no-sandbox",
                        "--disable-gpu",
                    ]
                    browser = p.chromium.launch(headless=True, args=launch_args)

                    ctx_kwargs = {
                        "user_agent": ua,
                        "viewport": vp,
                        "locale": "en-US",
                        "timezone_id": "Etc/UTC",
                    }
                    context = browser.new_context(**ctx_kwargs)

                    if self.stealth:
                        context.add_init_script(
                            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                        )

                    page = context.new_page()

                    # 🔥 FIX 1: dùng wait_until="domcontentloaded"
                    page.goto(url, timeout=self.pw_timeout, wait_until="domcontentloaded")

                    # 🔥 FIX 2: chờ body trước
                    try:
                        page.wait_for_selector("body", timeout=15000)
                    except:
                        logger.warning("[EventPageScraper] body not loaded — continue anyway")

                    # 🔥 FIX 3: human scroll để kích hoạt lazyload
                    self._humanize_page(page)
                    page.evaluate("window.scrollBy(0, document.body.scrollHeight / 2)")
                    time.sleep(0.3)
                    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    time.sleep(0.5)

                    html = page.content()

                    page.close()
                    context.close()
                    browser.close()

                if not html or len(html) < 200:
                    delay = backoff_delay(attempt, base=self.backoff_base)
                    logger.warning(f"[EventPageScraper] short html ({len(html)}), retry after {delay:.1f}s")
                    time.sleep(delay)
                    continue

                return html

            except Exception as e:
                delay = backoff_delay(attempt, base=self.backoff_base)
                logger.error(f"[EventPageScraper] Fetch error attempt {attempt}: {e}; backoff {delay:.1f}s")
                time.sleep(delay)

        return None

    def _parse_html(self, html: str, url: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        out: dict[str, Any] = {"article_url": url}

        # Title
        h1 = soup.select_one("h1")
        if h1:
            out["title"] = h1.get_text(strip=True)

        # Banner/OG image
        og = soup.select_one("meta[property='og:image']") or soup.select_one("meta[name='og:image']")
        if og and og.get("content"):
            out["banner_url"] = clean_banner_url(og.get("content"))
        else:
            img = soup.select_one(".entry-content img, .event-header img, .event-banner img")
            if img and img.get("src"):
                out["banner_url"] = clean_banner_url(img.get("src"))

        # Dates/time
        time_tag = soup.select_one("time")
        if time_tag and time_tag.get("datetime"):
            out["start_time"] = time_tag.get("datetime")
        elif time_tag:
            out["start_time"] = time_tag.get_text(strip=True)
        else:
            d = soup.select_one(".event-date, .date, .meta-date")
            if d:
                out["start_time"] = d.get_text(strip=True)

        # description (first paragraph)
        p = soup.select_one(".entry-content p, .article-content p, p")
        if p:
            out["description"] = p.get_text(" ", strip=True)

        # categories/tags
        cats = [a.get_text(strip=True) for a in soup.select(".category a, .tag a, a.tag")]
        if cats:
            out["categories"] = cats

        # details: try to capture key-value lists
        details = {}
        for row in soup.select(".event-details li, .event-meta li, .meta li"):
            try:
                text = row.get_text(" ", strip=True)
                if ":" in text:
                    k, v = text.split(":", 1)
                    details[k.strip()] = v.strip()
            except Exception:
                continue
        if details:
            out["details"] = details

        # images gallery
        imgs = [clean_banner_url(i.get("src")) for i in soup.select(".entry-content img") if i.get("src")]
        if imgs:
            out["images"] = imgs

        return out

    def scrape(self, url: str) -> Optional[dict[str, Any]]:
        html = self._fetch_html_with_playwright(url, attempt_limit=self.retries)
        if not html:
            return None
        try:
            return self._parse_html(html, url)
        except Exception as e:
            logger.exception(f"[EventPageScraper] parse error {e}")
            return None

    def close(self):
        # stateless implementation: nothing to close
        return
