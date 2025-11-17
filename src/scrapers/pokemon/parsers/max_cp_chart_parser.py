# max_cp_chart_parser.py

import re
from typing import Dict, Any
from bs4 import BeautifulSoup

from src.common.text_utils import clean_cp_text


def parse_max_cp_chart(html_or_tag) -> Dict[str, int]:
    """
    Parse Max CP Chart (Level 1 → 50).

    Output format:
    {
        "1": 59,
        "2": 185,
        ...
        "50": 4724
    }
    """

    # -----------------------------------------
    # Accept both string and BeautifulSoup Tag
    # -----------------------------------------
    if isinstance(html_or_tag, str):
        soup = BeautifulSoup(html_or_tag, "lxml")
        article = soup
    else:
        # it's already a Tag
        article = html_or_tag

    # -----------------------------------------
    # Find the table inside the article
    # -----------------------------------------
    table = article.select_one(".PokemonPageCPCharts_cpTable__huQC_ table")
    if not table:
        return {}

    result: Dict[str, int] = {}

    # table rows contain 3 pairs per row → (lvl, cp) x 3
    for tr in table.select("tbody tr"):
        cells = tr.find_all(["th", "td"])
        i = 0

        while i < len(cells):
            cell = cells[i]

            if cell.name == "th":
                # LEVEL
                text = cell.get_text(strip=True)
                m = re.search(r"\d+", text)
                if not m:
                    i += 1
                    continue

                level_key = m.group(0)  # keep as string key

                # CP (next td)
                if i + 1 < len(cells) and cells[i + 1].name == "td":
                    raw_cp = cells[i + 1].get_text(" ", strip=True)
                    clean = clean_cp_text(raw_cp)

                    try:
                        result[level_key] = int(clean)
                    except:
                        pass

                    i += 2
                else:
                    i += 1

            else:
                i += 1

    return result