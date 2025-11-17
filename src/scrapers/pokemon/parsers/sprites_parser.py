# sprites_parser.py
from typing import Dict, Any

from bs4 import BeautifulSoup

from src.common.normalize import normalize_url


def parse_sprites(html: str) -> Dict[str, Any]:
    """
    Parse GO Hub 'Sprites' section into:
    {
        "regular_shiny": [
            {
                "label": "Regular Mega Venusaur",
                "img": "...",
                "url": "...",
            },
            ...
        ],
        "home_sprites": [
            {
                "pokedex_number": 3,
                "img": "...",
                "url": "...",
                "alt": "...",
            },
            ...
        ],
        "wallpapers": [
            {
                "img": "...",
                "url": "...",
                "alt": "...",
            }
        ]
    }
    """

    soup = BeautifulSoup(html, "lxml")
    result = {
        "regular_shiny": [],
        "home_sprites": [],
        "wallpapers": [],
    }

    # ---------------------------------------------------------
    # 1) Regular + Shiny sprites
    # ---------------------------------------------------------
    ul = soup.select_one("ul.PokemonNormalAndShinyComparison_list__uUZTC")
    if ul:
        for li in ul.select("li"):
            a = li.select_one("a")
            img = li.select_one("img")
            label_tag = li.select_one("small")

            if not a or not img:
                continue

            result["regular_shiny"].append({
                "label": label_tag.get_text(strip=True) if label_tag else None,
                "img": normalize_url(img.get("src")),
                "url": normalize_url(a.get("href")),
            })

    # ---------------------------------------------------------
    # 2) Pokémon HOME high-resolution sprites
    # ---------------------------------------------------------
    home_ul = soup.find("ul", attrs={"style": lambda x: x and "grid-template-columns" in x})
    if home_ul:
        for li in home_ul.select("li"):
            a = li.select_one("a")
            img = li.select_one("img")
            num_tag = li.select_one(".PokemonOfficialImage_number__6e64b")

            if not a or not img:
                continue

            number = None
            if num_tag:
                try:
                    number = int(num_tag.get_text(strip=True).replace("#", ""))
                except:
                    number = None

            result["home_sprites"].append({
                "pokedex_number": number,
                "img": normalize_url(img.get("src")),
                "url": normalize_url(a.get("href")),
                "alt": img.get("alt", "").strip(),
            })

    # ---------------------------------------------------------
    # 3) Wallpapers
    # ---------------------------------------------------------
    grid = soup.find("div", attrs={"style": lambda x: x and "grid-template-columns" in x})
    if grid:
        for a in grid.select("a"):
            img = a.select_one("img")
            if not img:
                continue

            result["wallpapers"].append({
                "img": normalize_url(img.get("src")),
                "url": normalize_url(a.get("href")),
                "alt": img.get("alt", "").strip(),
            })

    return result
