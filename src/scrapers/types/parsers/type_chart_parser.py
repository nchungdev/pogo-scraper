"""
type_chart_parser.py

Extracts:
{
    "types": {
        "Fire": {
            "name": "Fire",
            "image": "...",
            "attack": {...},
            "defense": {...},
            "best_counters": [...]
        },
        ...
    }
}
"""

from bs4 import BeautifulSoup

from src.common.normalize import normalize_url

TYPE_ORDER = [
    "Normal", "Fighting", "Flying", "Poison", "Ground", "Rock",
    "Bug", "Ghost", "Steel", "Fire", "Water", "Grass", "Electric",
    "Psychic", "Ice", "Dragon", "Dark", "Fairy"
]


def _parse_multiplier(text: str) -> float:
    try:
        return round(float(text.replace("%", "")) / 100, 2)
    except:
        return 1.0


def parse_type_chart(soup: BeautifulSoup):
    table = soup.select_one(".type-chart_chartWrapper__9Q6xA table")
    if not table:
        print("[TypeChart] ERROR: Missing type chart table")
        return {"types": {}}

    # --------------------------------------------------------
    # Parse header: icons for each attacking type
    # --------------------------------------------------------
    header_cells = table.select("thead tr th")[1:]
    type_images = []
    for th in header_cells:
        img = th.select_one("img")
        raw = img["src"] if img else None
        type_images.append(normalize_url(raw))

    # --------------------------------------------------------
    # Build defensive matrix: defender → attacker → multiplier
    # --------------------------------------------------------
    rows = table.select("tbody tr")
    matrix = {t: {} for t in TYPE_ORDER}

    for row_idx, tr in enumerate(rows):
        defender = TYPE_ORDER[row_idx]
        for col_idx, td in enumerate(tr.select("td")):
            attacker = TYPE_ORDER[col_idx]
            mult = _parse_multiplier(td.get_text(strip=True))
            matrix[defender][attacker] = mult

    # --------------------------------------------------------
    # Build final JSON for each type
    # --------------------------------------------------------
    out = {}

    for i, t in enumerate(TYPE_ORDER):

        image = type_images[i]

        # DEFENSE
        weak, resist, immune = [], [], []

        for attacker, m in matrix[t].items():
            if m >= 1.6:
                weak.append(attacker)
            elif m == 0:
                immune.append(attacker)
            elif m <= 0.63:
                resist.append(attacker)

        # ATTACK
        sup_eff, not_eff, no_eff = [], [], []
        for defender in TYPE_ORDER:
            m = matrix[defender][t]
            if m >= 1.6:
                sup_eff.append(defender)
            elif m == 0:
                no_eff.append(defender)
            elif m <= 0.63:
                not_eff.append(defender)

        # BEST COUNTERS = types that deal SE to t AND resist it
        best = []
        for attacker in weak:
            retaliate = matrix[attacker][t]
            if retaliate <= 0.63:
                best.append({
                    "type": attacker,
                    "reason": f"{attacker} deals {matrix[t][attacker]}x and resists ({retaliate}x)"
                })

        out[t] = {
            "name": t,
            "image": image,
            "attack": {
                "super_effective": sup_eff,
                "not_very_effective": not_eff,
                "no_effect": no_eff,
            },
            "defense": {
                "weak_to": weak,
                "resistant_to": resist,
                "immune_to": immune,
            },
            "best_counters": best,
        }

    return {"results": out}
