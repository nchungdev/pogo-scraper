# moves/moves_scraper.py

import json

from playwright.sync_api import sync_playwright

from src.scrapers.moves.move_table_parser import parse_move_table

URLS = {
    "fast_pve": ("https://db.pokemongohub.net/moves-list/category-fast", False, False),
    "fast_pvp": ("https://db.pokemongohub.net/moves-list/pvp/category-fast", False, True),
    "charge_pve": ("https://db.pokemongohub.net/moves-list/category-charge", True, False),
    "charge_pvp": ("https://db.pokemongohub.net/moves-list/pvp/category-charge", True, True),
}


def fetch_html(url: str) -> str:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_selector("table", timeout=10000)
        html = page.content()
        browser.close()
    return html


def scrape_all_moves():
    fast = {}
    charge = {}

    for key, (url, is_charge, is_pvp) in URLS.items():
        print(f"[SCRAPING] {key}...")
        html = fetch_html(url)
        data = parse_move_table(html, is_charge=is_charge, is_pvp=is_pvp)

        for move_id, move_data in data.items():
            target = charge if is_charge else fast

            if move_id not in target:
                target[move_id] = move_data
            else:
                # merge pve/pvp
                if move_data["pve"]:
                    target[move_id]["pve"] = move_data["pve"]
                if move_data["pvp"]:
                    target[move_id]["pvp"] = move_data["pvp"]

    # save JSON
    with open("fast_moves.json", "w", encoding="utf-8") as f:
        json.dump(list(fast.values()), f, ensure_ascii=False, indent=2)

    with open("charge_moves.json", "w", encoding="utf-8") as f:
        json.dump(list(charge.values()), f, ensure_ascii=False, indent=2)

    print("[DONE] Saved fast_moves.json & charge_moves.json")
