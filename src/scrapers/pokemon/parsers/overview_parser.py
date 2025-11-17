import re
from typing import Dict

from bs4 import BeautifulSoup


def _snake_case(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\/\-\s]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s


def _normalize_value(v: str) -> str | int | float | bool | None:
    if not v:
        return None

    v = v.strip()

    # yes/no → bool
    low = v.lower()
    if low == "yes":
        return True
    if low == "no":
        return False

    # remove units (km, HP, ATK, DEF)
    v = re.sub(r"\b(km|hp|atk|def)\b", "", v, flags=re.I).strip()

    # CP
    v = re.sub(r"\bcp\b", "", v, flags=re.I).strip()

    # number?
    if v.isdigit():
        try:
            return int(v)
        except:
            pass

    return v


def parse_overview_stats(html: str) -> Dict[str, any]:
    soup = BeautifulSoup(html, "lxml")

    data = {}

    table = soup.select_one("table")
    if table:
        for tr in table.select("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue
            key = _snake_case(th.get_text(strip=True))
            raw = td.get_text(" ", strip=True)
            data[key] = _normalize_value(raw)

    # title
    title = soup.find(["h1", "h2"])
    if title:
        data["title"] = title.get_text(strip=True)

    return data
