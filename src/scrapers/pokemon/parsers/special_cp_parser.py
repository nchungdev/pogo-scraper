# special_cp_parser.py

import re
from bs4 import BeautifulSoup
from typing import Any, Dict

from src.common.text_utils import clean_cp_text


def parse_special_cp(html: str) -> Dict[str, Any]:
    """
    Parse Special CP section.

    Output format:
    {
        "overview": "...",
        "entries": [
            {
                "category": "Max CP",
                "cp": "1260",
                "level": 50,
                "iv_floor": "15/15/15",
                "level_text": "Level 50, 15/15/15 IVs",
                "weather_boosted": false
            }
        ],
        "more_info": []
    }
    """
    soup = BeautifulSoup(html, "lxml")

    result = {
        "overview": "",
        "entries": [],
        "more_info": [],
    }

    # -----------------------------------------
    # Helper: extract level, iv floor, weather
    # -----------------------------------------
    def extract_level_info(text: str):
        if not text:
            return None, None, None, False

        txt = text.strip()
        level_text = txt

        m_lvl = re.search(r"Level\s*[: ]*(\d+)", txt, re.I)
        level = int(m_lvl.group(1)) if m_lvl else None

        m_iv = re.search(r"(\d{1,2}/\d{1,2}/\d{1,2})", txt)
        iv_floor = m_iv.group(1) if m_iv else None

        weather = bool(re.search(r"weather\s*boost", txt, re.I))

        return level_text, level, iv_floor, weather

    # -----------------------------------------
    # Overview paragraph
    # -----------------------------------------
    header = soup.find(id="special-cp")
    if header:
        p = header.find_next("p")
        if p:
            result["overview"] = p.get_text(" ", strip=True)

    # -----------------------------------------
    # CP TABLE
    # -----------------------------------------
    table = soup.select_one(".PokemonPageCPCharts_cpTable__huQC_ table")
    if table:
        trs = table.select("tbody tr")
        i = 0
        current_cat = None

        while i < len(trs):
            tr = trs[i]
            th = tr.find("th")
            tds = tr.find_all("td")

            # --- New category row ---
            if th:
                strong = th.find("strong")
                if strong:
                    current_cat = strong.get_text(" ", strip=True)

                if tds:
                    # main td
                    td = tds[0]
                    small = td.find("small")
                    small_text = small.get_text(" ", strip=True) if small else None

                    full = td.get_text(" ", strip=True)
                    if small_text:
                        cp_raw = full.replace(small_text, "").strip(" -–—, ").strip()
                    else:
                        cp_raw = full.strip()

                    cp_clean = clean_cp_text(cp_raw)

                    level_text = None
                    level = None
                    iv_floor = None
                    weather = False

                    if small_text:
                        level_text, level, iv_floor, weather = extract_level_info(small_text)
                    else:
                        # check next row
                        if i + 1 < len(trs):
                            nxt = trs[i + 1]
                            if not nxt.find("th"):
                                nxt_td = nxt.find("td")
                                nxt_small = nxt_td.find("small") if nxt_td else None
                                if nxt_small:
                                    nxt_text = nxt_small.get_text(" ", strip=True)
                                    (
                                        level_text,
                                        level,
                                        iv_floor,
                                        weather,
                                    ) = extract_level_info(nxt_text)
                                    i += 1  # consume row

                    result["entries"].append(
                        {
                            "category": current_cat,
                            "cp": cp_clean,
                            "level": level,
                            "iv_floor": iv_floor,
                            "level_text": level_text,
                            "weather_boosted": weather,
                        }
                    )

            # --- continuation row (still same category)
            else:
                if current_cat and tds:
                    td = tds[0]
                    small = td.find("small")
                    small_text = small.get_text(" ", strip=True) if small else None

                    full = td.get_text(" ", strip=True)
                    if small_text:
                        cp_raw = full.replace(small_text, "").strip(" -–—, ").strip()
                    else:
                        cp_raw = full.strip()

                    cp_clean = clean_cp_text(cp_raw)

                    level_text, level, iv_floor, weather = extract_level_info(
                        small_text or cp_raw
                    )

                    result["entries"].append(
                        {
                            "category": current_cat,
                            "cp": cp_clean,
                            "level": level,
                            "iv_floor": iv_floor,
                            "level_text": level_text,
                            "weather_boosted": weather,
                        }
                    )

            i += 1

    # -----------------------------------------
    # More information (inside <details>)
    # -----------------------------------------
    details = soup.find("details")
    if details:
        for li in details.select("li"):
            result["more_info"].append(li.get_text(" ", strip=True))

    return result
