# pokedex_entries_parser.py
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup


def _clean_entry_text(text: str) -> str:
    """Cleanup newlines, weird spacing, &shy, control chars…"""
    text = text.replace("\n", " ")
    text = text.replace("\f", " ")
    text = text.replace("\u00ad", "")  # soft hyphen
    text = text.replace("&shy;", "")
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _split_versions(raw: str) -> List[str]:
    """
    Convert:
        "Red, Blue" → ["Red", "Blue"]
        "Diamond, Pearl, Platinum, Black, White" → [...]
        "Let's Go, Pikachu!, Let's Go, Eevee!" → [...]
    """
    parts = [v.strip() for v in raw.split(",") if v.strip()]
    return parts


def parse_pokedex_entries_table(html: str) -> List[Dict[str, Any]]:
    """
    Parse the GO Hub Pokédex entries table:
    - header <h1 id="pokedex">
    - table with version list + entry

    Returns:
    [
        {
            "versions": [...],
            "entry": "...",
        },
        ...
    ]
    """
    soup = BeautifulSoup(html, "lxml")
    header = soup.find(id="pokedex")
    if not header:
        return []

    article = header.find_parent("article")
    if not article:
        return []

    table = article.find("table")
    if not table:
        return []

    results = []

    for tr in table.select("tbody tr"):
        tds = tr.select("td")
        if len(tds) != 2:
            continue

        raw_versions = tds[0].get_text(" ", strip=True)
        raw_entry = tds[1].get_text(" ", strip=True)

        versions = _split_versions(raw_versions)
        entry = _clean_entry_text(raw_entry)

        results.append({
            "versions": versions,
            "entry": entry,
        })

    return results