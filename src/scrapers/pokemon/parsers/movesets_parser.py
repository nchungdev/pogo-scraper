# movesets_parser.py
import re
from typing import Dict, Any

from bs4 import BeautifulSoup

from src.common.normalize import normalize_url


# ----------------------------------------
# Helper: parse type effectiveness rows
# ----------------------------------------
def _parse_effectiveness(article):
    eff = {"super_effective": [], "not_very_effective": []}

    rows = article.select(".TypeChartOffensive_row__eEIW4")
    for row in rows:
        scalar = row.select_one(".TypeChartOffensive_scalar__t6QBs")
        if not scalar:
            continue

        scalar_val = scalar.get_text(strip=True).replace("%", "")
        try:
            value_num = float(scalar_val)
        except:
            value_num = None

        types = []
        for t in row.select(".TypeChartOffensive_gridTypes__18NrL li"):
            img = t.select_one("img")
            type_text = img.get("title") if img else None
            if type_text:
                types.append(type_text)

        classes = scalar.parent.get("class", [])
        if "super-effective" in classes:
            for t in types:
                eff["super_effective"].append({"type": t, "value": value_num})
        else:
            for t in types:
                eff["not_very_effective"].append({"type": t, "value": value_num})

    return eff


# ----------------------------------------
# Helper: parse GYM & RAID table
# ----------------------------------------
def _parse_gym_raid(article):
    result = {}
    header = article.find("header", string=lambda x: x and "Gym" in x)
    if not header:
        return result

    table = header.find_next("table")
    if not table:
        return result

    for tr in table.select("tr"):
        key = tr.find("th").get_text(strip=True)
        val_td = tr.find("td")

        if key == "Weather boost":
            result["weather_boost"] = [
                i.get("alt") for i in val_td.select("img[alt]")
            ]
        elif key == "Duration":
            raw = val_td.text.strip().replace("s", "")
            try:
                result["duration"] = float(raw)
            except:
                result["duration"] = raw
        elif key == "Damage window":
            result["damage_window"] = val_td.get_text(" ", strip=True)
        else:
            txt = val_td.get_text(strip=True)
            try:
                result[key.lower()] = int(txt)
            except:
                result[key.lower()] = txt

    return result


# ----------------------------------------
# Helper: parse TRAINER BATTLES table
# ----------------------------------------
def _parse_trainer_battle(article):
    result = {}
    header = article.find("header", string=lambda x: x and "Trainer" in x)
    if not header:
        return result

    table = header.find_next("table")
    if not table:
        return result

    for tr in table.select("tr"):
        key = tr.find("th").get_text(strip=True)
        val = tr.find("td").text.strip()
        try:
            result[key.lower()] = int(val)
        except:
            result[key.lower()] = val

    return result


# ----------------------------------------
# FULL MOVE CARD PARSER (fast + charged)
# ----------------------------------------
def _parse_move_cards(ul):
    moves = []

    for li in ul.select("li"):
        try:
            details = li.select_one("details")
            if not details:
                continue

            summary = details.select_one("summary")
            article = details.select_one("article")

            # -------------------------
            # NAME + TYPE
            # -------------------------
            name_tag = summary.select_one(".MoveCard_name__M3I5R")
            name = name_tag.get_text(" ", strip=True)

            img_type = name_tag.select_one("img")
            type_name = img_type.get("title") if img_type else None

            # -------------------------
            # BASIC STATS (damage/energy/duration)
            # -------------------------
            stats_block = summary.select_one(".MoveCard_stats__MAgqA")
            spans = stats_block.select("span span") if stats_block else []

            damage = int(spans[0].text) if len(spans) > 0 else None
            energy = int(spans[1].text) if len(spans) > 1 else None

            duration_raw = spans[2].text if len(spans) > 2 else None
            duration = (
                float(duration_raw.replace("s", "")) if duration_raw else None
            )

            # -------------------------
            # Effectiveness chart
            # -------------------------
            effectiveness = _parse_effectiveness(article)

            # -------------------------
            # Gym/Raid
            # -------------------------
            gym_raid = _parse_gym_raid(article)

            # -------------------------
            # Trainer Battles
            # -------------------------
            trainer_battle = _parse_trainer_battle(article)

            # -------------------------
            # Final link (details page)
            # -------------------------
            url_tag = article.select_one("a[href]")
            move_url = normalize_url(url_tag.get("href")) if url_tag else None

            moves.append(
                {
                    "name": name,
                    "type": type_name,
                    "stats": {
                        "damage": damage,
                        "energy": energy,
                        "duration": duration,
                    },
                    "effectiveness": effectiveness,
                    "gym_raid": gym_raid,
                    "trainer_battle": trainer_battle,
                    "url": move_url,
                }
            )
        except Exception as e:
            print("[WARN] move card parse error:", e)

    return moves


# =====================================================================
# MAIN ENTRY — parse_movesets()
# =====================================================================
def parse_movesets(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")

    out = {
        "best_moveset": None,
        "detailed_combinations": [],
        "fast_moves": [],
        "charged_moves": [],
    }

    # ----------------------------------------------------
    # A. BEST MOVESET
    # ----------------------------------------------------
    try:
        card = soup.select_one(".MovesetCard_header__KtH6c")
        best = {"fast": None, "charged": None, "dps": None, "tdo": None, "boosted_weather": []}

        if card:
            text = card.get_text(" ", strip=True)
            m = re.search(
                r"best moveset is\s+(.+?)\s+and\s+(.+?)(?:,|\swith|\s$)", text, re.I
            )
            if m:
                best["fast"] = m.group(1).strip()
                best["charged"] = m.group(2).strip()

        # stats
        for li in soup.select(".MovesetCard_stats__3Czln li"):
            label = li.select_one("span")
            strong = li.select_one("strong")
            if not label or not strong:
                continue

            key = label.get_text(strip=True).lower()
            val = strong.get_text(" ", strip=True)

            if key.startswith("dps"):
                try:
                    best["dps"] = float(val)
                except:
                    pass
            elif key.startswith("tdo"):
                try:
                    best["tdo"] = float(val)
                except:
                    pass
            elif "weather" in key:
                imgs = li.select("img[alt]")
                best["boosted_weather"] = [i.get("alt") for i in imgs]

        out["best_moveset"] = best

    except Exception as e:
        print("[WARN] best moveset parse failed:", e)

    # ----------------------------------------------------
    # B. DETAILED COMBINATIONS TABLE
    # ----------------------------------------------------
    try:
        table = soup.select_one(
            "section.DataGrid_dataGridWrapper__G48Cu table.DataGrid_dataGrid__Q3gQi"
        )
        if table:
            for tr in table.select("tbody tr"):
                tds = tr.select("td")
                if len(tds) < 6:
                    continue

                def _cell(td):
                    a = td.select_one("a.MoveChip_moveChip__p9x2L")
                    if a:
                        return {
                            "name": a.get_text(" ", strip=True),
                            "url": normalize_url(a.get("href")),
                        }
                    return {"name": td.get_text(" ", strip=True), "url": None}

                rank = tds[0].text.strip().strip(".")
                rank = int(rank) if rank.isdigit() else rank

                fast = _cell(tds[1])
                charged = _cell(tds[2])

                def ff(x):
                    try:
                        return float(x)
                    except:
                        return None

                out["detailed_combinations"].append(
                    {
                        "rank": rank,
                        "fast": fast["name"],
                        "fast_url": fast["url"],
                        "charged": charged["name"],
                        "charged_url": charged["url"],
                        "dps": ff(tds[3].text.strip()),
                        "tdo": ff(tds[4].text.strip()),
                        "score": ff(tds[5].text.strip()),
                    }
                )
    except Exception as e:
        print("[WARN] detailed moveset parse failed:", e)

    # ----------------------------------------------------
    # C. FULL FAST / CHARGED MOVES PARSER (NEW)
    # ----------------------------------------------------
    fast_header = soup.find(
        lambda tag: tag.name in ("h2", "h3", "h4") and "fast attack" in tag.get_text(" ", strip=True).lower())
    charged_header = soup.find(
        lambda tag: tag.name in ("h2", "h3", "h4") and "charged" in tag.get_text(" ", strip=True).lower())

    # fast moves
    if fast_header:
        ul = fast_header.find_next("ul", class_="PokemonPageMoves_movesList__L7k6W")
        if ul:
            out["fast_moves"] = _parse_move_cards(ul)

    # charged moves
    if charged_header:
        ul = charged_header.find_next("ul", class_="PokemonPageMoves_movesList__L7k6W")
        if ul:
            out["charged_moves"] = _parse_move_cards(ul)

    return out
