from typing import List, Dict

from bs4 import BeautifulSoup

from src.common.normalize import normalize_url


def parse_forms(soup: BeautifulSoup, url_norm=normalize_url) -> List[Dict]:
    out = []

    selected = soup.select_one(".CoreSelect_selectedItemLabel__tPXIX a")
    selected_href = None

    if selected:
        name = selected.get_text(strip=True)
        href = selected.get("href")
        selected_href = href
        img = selected.select_one("img")
        thumb = url_norm(img.get("src")) if img else None
        out.append({"name": name, "href": href, "thumbnail": thumb})

    for a in soup.select("ul.CoreSelect_options__1ndcB li a"):
        name = a.get_text(strip=True)
        href = a.get("href")
        if href == selected_href and out and name == out[0]["name"]:
            continue

        imgs = a.select("img")
        if len(imgs) >= 2:
            thumb = url_norm(imgs[1].get("src"))
        elif len(imgs) == 1:
            thumb = url_norm(imgs[0].get("src"))
        else:
            thumb = None

        out.append({"name": name, "href": href, "thumbnail": thumb})

    return out


def parse_official_art(soup: BeautifulSoup, url_norm=normalize_url) -> str | None:
    img = soup.select_one(".PokemonOfficialImage_image__BE1nh img")
    return url_norm(img.get("src")) if img else None


def parse_types(soup: BeautifulSoup) -> List[str]:
    VALID = {
        "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison",
        "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dark", "Dragon",
        "Steel", "Fairy"
    }

    # Best container
    container = soup.select_one(
        "div.PokemonPageRenderers_officialImage__IFm7y span.PokemonPageRenderers_officialImageTyping__BZQBp"
    )

    imgs = container.select("img") if container else soup.select(
        ".PokemonPageRenderers_officialImageTyping__BZQBp img, .PokemonTyping_typing__VyONk img"
    )

    out = []
    for img in imgs:
        alt = (img.get("alt") or img.get("title") or "").strip().capitalize()
        if alt in VALID and alt not in out:
            out.append(alt)

    return out


def parse_weather_boost(soup: BeautifulSoup) -> List[str]:
    imgs = soup.select(
        "div.PokemonPageRenderers_leftOrnament__RVx6P .WeatherInfluences_weatherInfluences__mxolf img"
    )
    return [img.get("alt", "").strip() for img in imgs]


def parse_availability_flags(soup: BeautifulSoup) -> Dict[str, bool]:
    avail = False
    shiny = False
    dynamax = False

    for img in soup.select(".PokemonPageRenderers_rightOrnament__t2nwE img"):
        alt = (img.get("alt") or "").lower()
        if "available in pokémon go" in alt or "available in pokemon go" in alt:
            avail = True
        if "shiny" in alt:
            shiny = True
        if "dynamax" in alt:
            dynamax = True

    return {
        "available_in_pogo": avail,
        "shiny_available": shiny,
        "can_dynamax": dynamax
    }
