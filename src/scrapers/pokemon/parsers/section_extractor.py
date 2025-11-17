from typing import Optional, List

from bs4 import BeautifulSoup


def extract_section_html(soup: BeautifulSoup, section_id: str) -> Optional[str]:
    hdr = soup.find(id=section_id)
    if not hdr:
        return None

    # Prefer wrapping <article>
    article = hdr.find_parent("article")
    if article:
        return str(article)

    # Fallback: grab header + nodes until next header
    out: List[str] = []
    for node in hdr.find_all_next():
        if node.name in ("h2", "h3") and node.get("id") != section_id:
            break
        out.append(str(node))

    return "\n".join(out)
