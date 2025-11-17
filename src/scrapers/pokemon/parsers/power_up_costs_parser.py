# power_up_costs_parser.py
from bs4 import BeautifulSoup
from typing import Dict, Any
import re


def _num(x):
    m = re.findall(r"[\d,]+", x)
    if not m:
        return None
    return int(m[0].replace(",", ""))


def parse_power_up_costs(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")

    result = {
        "power_up_simple": [],
        "power_up_full": []
    }

    # First table – simple LVL 50, 40, 35, 30, ...
    simple_container = soup.find("div", class_="PokemonPagePowerUpChart_powerUpTableContainer__IK_xN")
    if simple_container:
        tbl = simple_container.find("table", class_="PokemonPagePowerUpChart_powerUpTable__dCnbj")
        if tbl:
            for tr in tbl.select("tbody tr"):
                th = tr.find("th")
                tds = tr.find_all("td")
                if not th or len(tds) < 3:
                    continue

                level = _num(th.get_text(strip=True))
                sd = _num(tds[0].get_text(strip=True))
                candy = _num(tds[1].get_text(strip=True))
                candy_xl = _num(tds[2].get_text(strip=True))

                result["power_up_simple"].append({
                    "level": level,
                    "stardust": sd,
                    "candy": candy,
                    "candy_xl": candy_xl
                })

    # Complete Power Up Table (inside <details open>)
    full_details = soup.find("details", open=True)
    if full_details:
        tbl = full_details.find("table")
        if tbl:
            for tr in tbl.select("tbody tr"):
                th = tr.find("th")
                tds = tr.find_all("td")
                if not th or len(tds) < 7:
                    continue

                result["power_up_full"].append({
                    "level": _num(th.get_text(strip=True)),
                    "powerups": _num(tds[0].get_text(strip=True)),
                    "stardust": _num(tds[1].get_text(strip=True)),
                    "candy": _num(tds[2].get_text(strip=True)),
                    "candy_xl": _num(tds[3].get_text(strip=True)),
                    "total_stardust": _num(tds[4].get_text(strip=True)),
                    "total_candy": _num(tds[5].get_text(strip=True)),
                    "total_candy_xl": _num(tds[6].get_text(strip=True)),
                })

    return result