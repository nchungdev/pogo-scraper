from typing import Dict

from bs4 import BeautifulSoup

from src.common.normalize import normalize_url


# ------------------- Evolution -------------------
def parse_evolution(html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")
    out = {"stages": [], "details": [], "family": []}

    header = soup.find(id="evolution-chart")
    if not header:
        return out
    article = header.find_parent("article")
    if not article:
        return out

    def chip(a):
        if not a:
            return None
        name = a.get_text(" ", strip=True)
        href = a.get("href")
        img_tag = a.select_one("img")
        img = normalize_url(img_tag.get("src")) if img_tag else None
        return {"name": name, "href": href, "img": img}

    table = article.select_one(".EvolutionChart_evolutionChart__h4JQ_ table")
    if table:
        for tr in table.select("tbody tr"):
            tds = tr.find_all("td")
            if len(tds) != 3:
                continue
            out["stages"].append({
                "from": chip(tds[0].select_one("a")),
                "to": chip(tds[2].select_one("a")),
                "requirements": [li.get_text(" ", strip=True) for li in tds[1].select("li")]
            })

    # details
    ul = article.find("ul")
    if ul:
        for li in ul.find_all("li", recursive=False):
            out["details"].append(li.get_text(" ", strip=True))

    # family
    fam = article.select_one(".PokemonFamily_pokemonFamily__W_zoW")
    if fam:
        for it in fam.select("a"):
            c = chip(it)
            if c:
                out["family"].append(c)

    return out
