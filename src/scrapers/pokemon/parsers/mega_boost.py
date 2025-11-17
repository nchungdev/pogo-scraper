# mega_boost_parser.py
import re
from typing import Dict, Any, List

from bs4 import BeautifulSoup

from src.common.normalize import normalize_url


def parse_mega_boost(html: str) -> Dict[str, Any]:
    """
    Parse Mega Boost section:
    - title
    - type icon name (e.g., Psychic)
    - intro text
    - list of Mega Pokémon that boost this Pokémon
    - bonus info (raid bonus, catch bonus)
    - primal notes (Kyogre/Groudon/Rayquaza boosts)
    """

    soup = BeautifulSoup(html, "lxml")

    # ---------------------------------------------------------
    # 1) Find the main <article> via header id="mega-boost"
    # ---------------------------------------------------------
    header = soup.find("h1", id="mega-boost")
    if not header:
        return {}

    article = header.find_parent("article")
    if not article:
        return {}

    result = {
        "title": header.get_text(strip=True),
        "type": None,
        "intro_text": None,
        "mega_list": [],
        "bonus_info": {},
        "primal_notes": {},
    }

    # ---------------------------------------------------------
    # 2) Type header: <h3><img ...> Psychic</h3>
    # ---------------------------------------------------------
    type_h3 = article.find("h3")
    if type_h3:
        # the text after icon
        result["type"] = type_h3.get_text(" ", strip=True)

    # ---------------------------------------------------------
    # 3) Intro text = the <p> immediately after <h1>
    # ---------------------------------------------------------
    intro_p = header.find_next("p")
    if intro_p:
        result["intro_text"] = intro_p.get_text(" ", strip=True)

    # ---------------------------------------------------------
    # 4) Mega list grid
    # <ul class="PokemonMegaBoost_megaBoostGridList__flSNO"><li>...</li></ul>
    # ---------------------------------------------------------
    grid_ul = article.select_one("ul.PokemonMegaBoost_megaBoostGridList__flSNO")
    if grid_ul:
        for li in grid_ul.find_all("li", recursive=False):
            try:
                a = li.find("a", href=True)
                if not a:
                    continue

                url = normalize_url(a["href"])
                name = a.get_text(" ", strip=True)

                # extract pokemon id from URL: /pokemon/65-Mega
                m = re.search(r"/pokemon/(\d+)", url)
                pokemon_id = int(m.group(1)) if m else None

                # detect form: "-Mega", "-MegaY", etc.
                form = None
                fm = re.search(r"/pokemon/\d+-(.+)$", url)
                if fm:
                    form = fm.group(1)

                # official artwork image
                img = li.select_one("img[data-nimg]")
                img_url = normalize_url(img["src"]) if img else None

                result["mega_list"].append({
                    "name": name,
                    "pokemon_id": pokemon_id,
                    "form": form,
                    "url": url,
                    "image": img_url,
                })
            except:
                pass

    # ---------------------------------------------------------
    # 5) Bonus info & Primal notes inside <details>
    # ---------------------------------------------------------
    details = article.find("details")
    if details:
        # Get paragraphs first
        ps = details.find_all("p", recursive=False)
        if ps:
            # raid bonus
            if len(ps) >= 1:
                result["bonus_info"]["raid_bonus"] = ps[0].get_text(" ", strip=True)
            # catch bonus
            if len(ps) >= 2:
                result["bonus_info"]["catch_bonus"] = ps[1].get_text(" ", strip=True)

        # Primal notes (ul)
        ul = details.find("ul")
        if ul:
            notes = ul.find_all("li")
            for li in notes:
                txt = li.get_text(" ", strip=True)

                # Kyogre
                if txt.lower().startswith("primal kyogre"):
                    arr = _extract_types_from_line(txt)
                    result["primal_notes"]["primal_kyogre"] = arr

                # Groudon
                elif txt.lower().startswith("primal groudon"):
                    arr = _extract_types_from_line(txt)
                    result["primal_notes"]["primal_groudon"] = arr

                # Rayquaza
                elif txt.lower().startswith("mega rayquaza"):
                    arr = _extract_types_from_line(txt)
                    result["primal_notes"]["mega_rayquaza"] = arr

    return result


# ---------------------------------------------------------
# Helper: parse "boosts Fire-, Grass- and Ground-type"
# ---------------------------------------------------------
def _extract_types_from_line(text: str) -> List[str]:
    """
    Convert:
      "Primal Groudon boosts Fire-, Grass- and Ground-type"
    → ["Fire", "Grass", "Ground"]
    """
    # remove prefix
    text = text.split("boosts", 1)[-1]

    # remove "-type"
    text = text.replace("-type", "")

    # split by comma or "and"
    parts = re.split(r",|and", text)
    cleaned = [p.strip().rstrip("-") for p in parts if p.strip()]
    return cleaned
