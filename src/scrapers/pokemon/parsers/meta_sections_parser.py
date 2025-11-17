# meta_sections_parser.py

from typing import Dict, List

from bs4 import BeautifulSoup


def parse_meta_analysis(html: str) -> str:
    return BeautifulSoup(html, "lxml").get_text(" ", strip=True)


def parse_faq(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    out = []

    for h in soup.select("h3"):
        q = h.get_text(strip=True)
        ans = []
        for sib in h.find_next_siblings():
            if sib.name == "h3":
                break
            ans.append(sib.get_text(" ", strip=True))
        out.append({"question": q, "answer": " ".join(ans).strip()})

    return out
