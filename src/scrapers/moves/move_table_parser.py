# moves/move_table_parser.py

from bs4 import BeautifulSoup

from src.common.normalize import normalize_url


def parse_move_table(html: str, is_charge: bool, is_pvp: bool):
    soup = BeautifulSoup(html, "lxml")

    rows = soup.select("table tbody tr")
    moves = {}

    for tr in rows:
        cells = tr.find_all("td")
        if not cells:
            continue

        # =============== NAME + ID + ICON + TYPE ===============
        a = cells[0].select_one("a")
        href = a.get("href")
        move_id = int(href.split("/")[-1])

        img = a.select_one("img")
        type_name = img.get("title")
        icon = normalize_url(img.get("src"))

        name = a.get_text(strip=True)

        # Create base object
        if move_id not in moves:
            moves[move_id] = {
                "id": move_id,
                "name": name,
                "type": type_name,
                "icon": icon,
                "pve": None,
                "pvp": None,
            }

        # =============== PARSE PVE ===============
        if not is_pvp:
            # FAST MOVE PvE: Name, PWR, ENG, Duration, DPS
            # CHARGE MOVE PvE: Name, PWR, ENG, Duration, DPS
            moves[move_id]["pve"] = {
                "power": safe_num(cells[1].text),
                "energy": safe_num(cells[2].text),
                "duration": cells[3].text.strip(),
                "dps": safe_num(cells[4].text),
            }

        # =============== PARSE PVP ===============
        else:
            if is_charge:
                # charge pvp: Name, DPE, PWR, ENG
                moves[move_id]["pvp"] = {
                    "dpe": safe_num(cells[1].text),
                    "power": safe_num(cells[2].text),
                    "energy": safe_num(cells[3].text),
                }
            else:
                # fast pvp: Name, DPT, EPT, Turns
                moves[move_id]["pvp"] = {
                    "dpt": safe_num(cells[1].text),
                    "ept": safe_num(cells[2].text),
                    "turns": safe_num(cells[3].text),
                }

    return moves


def safe_num(s: str):
    s = s.replace("-", "").strip()
    try:
        return float(s) if "." in s else int(s)
    except:
        return None
