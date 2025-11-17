# costumes_parser.py
from typing import Dict, Any, List

from bs4 import BeautifulSoup

from src.common.normalize import normalize_url


def parse_costumes(html: str) -> List[Dict[str, Any]]:
    """
    Parse GO Hub 'List of <Pokemon> costumes' section.

    Returns:
    [
        {
            "pokedex_number": 1,
            "name": "Bulbasaur",
            "shiny": False,
            "img": "...",
            "url": "...",
            "category": "Jan 2020"
        },
        ...
    ]
    """

    soup = BeautifulSoup(html, "lxml")
    result: List[Dict[str, Any]] = []

    # Find the grid <ul> (it always uses inline CSS grid)
    ul = soup.find("ul", attrs={"style": lambda x: x and "grid-template-columns" in x})
    if not ul:
        return result

    for li in ul.select("li"):
        a = li.select_one("a")
        if not a:
            continue

        img = li.select_one("img")
        num_tag = li.select_one(".PokemonOfficialImage_number__6e64b")
        small_tags = li.select("small")

        # Parse pokédex number
        number = None
        if num_tag:
            try:
                number = int(num_tag.get_text(strip=True).replace("#", ""))
            except:
                number = None

        # Parse costume name + category
        name = None
        category = None
        shiny = False

        if small_tags:
            # General rule:
            # small[0] = name (Bulbasaur, Shiny Bulbasaur)
            # small[1] = category (Jan 2020, Spring 2020…)
            if len(small_tags) >= 1:
                name = small_tags[0].get_text(strip=True)
                if "shiny" in name.lower():
                    shiny = True
            if len(small_tags) >= 2:
                category = small_tags[1].get_text(strip=True)

        result.append(
            {
                "pokedex_number": number,
                "name": name,
                "shiny": shiny,
                "img": normalize_url(img.get("src")) if img else None,
                "url": normalize_url(a.get("href")) if a else None,
                "category": category,
            }
        )

    return result
