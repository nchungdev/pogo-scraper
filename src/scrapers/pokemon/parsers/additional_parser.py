# additional_parser.py
"""
Robust pokedex parser for Pokémon GO Hub "Pokédex information" article.
- Self-contained _normalize_value to avoid import path issues.
- Works with the HTML snippet provided (h1 id="additional" inside article header).
- Returns structured dict:
  {
    "basic_info": {...},
    "catch_rewards": {...},
    "additional_move_cost": {...},
    "mega_energy_reward": int|None,
    "size_info": {...},
    "size_bounds": [...],
    "encounter_data": {...}
  }
"""
import re
from typing import Dict, Any, Optional

from bs4 import BeautifulSoup


def _snake_case(text: str) -> str:
    s = (text or "").strip().lower()
    s = re.sub(r"[\/\-\s]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _to_number_if_possible(text: str):
    """Try to convert strings like '10', '5%', '#3', '1.18 m' to int/float when sensible.
       Keep original string if ambiguous (e.g., 'MOVEMENT_JUMP', '3′10″').
    """
    if text is None:
        return None
    t = text.strip()

    # Plain percent -> float (e.g. "5%")
    m_pct = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*%$", t)
    if m_pct:
        val = float(m_pct.group(1))
        return val

    # Hash number e.g. "#3"
    m_hash = re.match(r"^#\s*([0-9]+)$", t)
    if m_hash:
        return int(m_hash.group(1))

    # simple integer
    m_int = re.match(r"^[0-9]+$", t)
    if m_int:
        return int(t)

    # float with unit m / kg e.g. "2.4 m", "155.5 kg"
    m_unit_num = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(m|kg|km)?$", t, re.I)
    if m_unit_num:
        num = m_unit_num.group(1)
        if "." in num:
            return float(num)
        else:
            return int(num)

    # time in seconds "11s" or "0.5s"
    m_s = re.match(r"^([0-9]+(?:\.[0-9]+)?)s$", t, re.I)
    if m_s:
        num = m_s.group(1)
        return float(num) if "." in num else int(num)

    # numbers embedded in text like "15 Mega Energy" or "500"
    m_num = re.search(r"([0-9]+(?:\.[0-9]+)?)", t)
    if m_num and t.lower().startswith(m_num.group(1)):
        # if it starts with number, return numeric
        num = m_num.group(1)
        return float(num) if "." in num else int(num)

    # boolean likeness
    if t.lower() in ("yes", "true", "allowed", "available"):
        return True
    if t.lower() in ("no", "false", "not allowed", "forbidden"):
        return False

    # fallback: keep original trimmed string
    return t


def _normalize_value(text: Optional[str]):
    """Wrapper to clean and convert common UI values."""
    if text is None:
        return None
    t = text.strip()

    # remove extra inline markers/newlines
    t = re.sub(r"\s+", " ", t)

    # remove commas from numbers like "1,000" before numeric parse
    t_clean = t.replace(",", "")

    val = _to_number_if_possible(t_clean)
    return val


def parse_additional(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")

    # Find the article that holds Pokédex info
    header_h = soup.find(id="additional")
    if header_h:
        article = header_h.find_parent("article")
    else:
        # fallback: find article with header containing "Pokédex"
        article = None
        for art in soup.find_all("article"):
            h = art.find(["h1", "h2", "h3"])
            if h and "pokedex" in h.get_text(" ", strip=True).lower():
                article = art
                break

    if not article:
        # nothing to parse
        return {}

    result: Dict[str, Any] = {
        "basic_info": {},
        "catch_rewards": {},
        "additional_move_cost": {},
        "mega_energy_reward": None,
        "size_info": {},
        "size_bounds": [],
        "encounter_data": {},
    }

    # ---------- A) BASIC INFO TABLE (first table under the article) ----------
    tables = article.find_all("table")
    if tables:
        basic_table = tables[0]
        for tr in basic_table.select("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue

            raw_key = th.get_text(" ", strip=True)
            key_norm = raw_key.strip().lower()
            raw_val = td.get_text(" ", strip=True)

            # handle common keys (normalize accented words)
            key_simple = key_norm.replace("\n", " ").strip()

            # Catch rewards block (contains badges)
            if key_simple.startswith("catch rewards"):
                # find spans that include the value (image + value text)
                for span in td.select(".PokemonPageRenderers_inlineTitle__Icmvi"):
                    img = span.find("img")
                    txt = span.get_text(" ", strip=True)
                    if not img:
                        continue
                    alt = (img.get("alt") or "").lower()
                    if "candy" in alt:
                        result["catch_rewards"]["candy"] = _normalize_value(txt)
                    elif "stardust" in alt:
                        result["catch_rewards"]["stardust"] = _normalize_value(txt)
                continue

            # Additional Move Cost (similar structure)
            if key_simple.startswith("additional move cost") or key_simple.startswith("additional"):
                for span in td.select(".PokemonPageRenderers_inlineTitle__Icmvi"):
                    img = span.find("img")
                    txt = span.get_text(" ", strip=True)
                    if not img:
                        continue
                    alt = (img.get("alt") or "").lower()
                    if "candy" in alt:
                        result["additional_move_cost"]["candy"] = _normalize_value(txt)
                    elif "stardust" in alt:
                        result["additional_move_cost"]["stardust"] = _normalize_value(txt)
                continue

            # Mega energy reward row
            if key_simple.startswith("mega energy reward"):
                span = td.select_one(".PokemonPageRenderers_inlineTitle__Icmvi")
                if span:
                    txt = span.get_text(" ", strip=True)
                    m = re.search(r"([0-9]+)", txt)
                    if m:
                        result["mega_energy_reward"] = int(m.group(1))
                else:
                    # fallback: try to extract number from raw_val
                    m = re.search(r"([0-9]+)", raw_val)
                    if m:
                        result["mega_energy_reward"] = int(m.group(1))
                continue

            # Generic simple keys
            if key_simple.startswith("pokédex number") or key_simple.startswith("pokedex number"):
                result["basic_info"]["pokedex_number"] = _normalize_value(raw_val)
            elif key_simple.startswith("height"):
                # keep meters numeric if possible
                result["basic_info"]["height_m"] = _normalize_value(raw_val)
            elif key_simple.startswith("weight"):
                result["basic_info"]["weight_kg"] = _normalize_value(raw_val)
            elif key_simple.startswith("region"):
                # use the anchor text if present
                a = td.find("a")
                if a:
                    result["basic_info"]["region"] = a.get_text(" ", strip=True)
                else:
                    result["basic_info"]["region"] = raw_val
            elif key_simple.startswith("can be traded"):
                result["basic_info"]["can_be_traded"] = True if raw_val.strip().lower() in ("allowed", "yes",
                                                                                            "available",
                                                                                            "true") else False
            elif key_simple.startswith("pokémon home transfer") or key_simple.startswith("pokemon home transfer"):
                result["basic_info"]["pokemon_home_transfer"] = True if raw_val.strip().lower() in ("allowed", "yes",
                                                                                                    "available",
                                                                                                    "true") else False
            elif key_simple.startswith("base catch rate"):
                result["basic_info"]["base_catch_rate"] = _normalize_value(raw_val)
            elif key_simple.startswith("base flee rate"):
                result["basic_info"]["base_flee_rate"] = _normalize_value(raw_val)
            else:
                # put unknowns under basic_info with snake_case key
                sk = _snake_case(key_simple)
                result["basic_info"].setdefault(sk, _normalize_value(raw_val))

    # ---------- B) SIZE INFORMATION ----------
    size_h3 = article.find(lambda tag: tag.name in ("h3", "h2") and "Size information".lower() in (
                tag.get_text(" ", strip=True) or "").lower())
    if size_h3:
        size_table = size_h3.find_next("table")
        if size_table:
            tbody_rows = size_table.select("tbody tr")
            # find row that contains meters (cells with "m")
            cm_row = None
            for r in tbody_rows:
                texts = [td.get_text(" ", strip=True) for td in r.find_all("td")]
                if any("m" in (t or "").lower() for t in texts):
                    cm_row = r
                    break
            if cm_row:
                cm_cells = cm_row.find_all("td")
                sizes = ["xxs", "xs", "m", "xl", "xxl"]
                for i, s in enumerate(sizes):
                    if i < len(cm_cells):
                        result["size_info"][s] = cm_cells[i].get_text(" ", strip=True)
        # description paragraph after header
        desc = size_h3.find_next("p")
        if desc:
            result["size_info"]["description"] = desc.get_text(" ", strip=True)

    # ---------- C) SIZE BOUNDS ----------
    bounds_h4 = article.find(
        lambda tag: tag.name == "h4" and "Size bounds".lower() in (tag.get_text(" ", strip=True) or "").lower())
    if bounds_h4:
        bounds_table = bounds_h4.find_next("table")
        if bounds_table:
            trs = bounds_table.select("tbody tr")
            i = 0
            while i < len(trs) - 1:
                tr1 = trs[i]
                tr2 = trs[i + 1]
                th = tr1.find("th")
                if not th:
                    i += 1
                    continue
                size_name = th.get_text(" ", strip=True)
                tds1 = tr1.find_all("td")
                tds2 = tr2.find_all("td")
                lower_m = _normalize_value(tds1[0].get_text(" ", strip=True)) if len(tds1) > 0 else None
                upper_m = _normalize_value(tds1[1].get_text(" ", strip=True)) if len(tds1) > 1 else None
                lower_ft = tds2[0].get_text(" ", strip=True) if len(tds2) > 0 else None
                upper_ft = tds2[1].get_text(" ", strip=True) if len(tds2) > 1 else None

                result["size_bounds"].append({
                    "size": size_name,
                    "lower_m": lower_m,
                    "upper_m": upper_m,
                    "lower_ft": lower_ft,
                    "upper_ft": upper_ft,
                })
                i += 2

    # ---------- D) ENCOUNTER DATA ----------
    enc_h3 = article.find(lambda tag: tag.name in ("h3", "h2") and "Encounter data".lower() in (
                tag.get_text(" ", strip=True) or "").lower())
    if enc_h3:
        enc_table = enc_h3.find_next("table")
        if enc_table:
            for tr in enc_table.select("tr"):
                th = tr.find("th")
                td = tr.find("td")
                if not th or not td:
                    continue
                raw_k = th.get_text(" ", strip=True)
                raw_v = td.get_text(" ", strip=True)

                key = _snake_case(raw_k)
                # If the value ends with 's' (seconds) keep numeric but add suffix to key
                if re.match(r"^[0-9]+(?:\.[0-9]+)?s$", raw_v.strip(), re.I):
                    norm_v = _normalize_value(raw_v)
                    key = key + "_s"
                else:
                    norm_v = _normalize_value(raw_v)

                result["encounter_data"][key] = norm_v

    return result