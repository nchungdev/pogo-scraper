from typing import Optional
from urllib.parse import urljoin

BASE = "https://db.pokemongohub.net"


# -----------------------------------------------------------------------
# URL NORMALIZER (dedupe từ file 1, để PokemonDetailScraper xài trực tiếp)
# -----------------------------------------------------------------------
def normalize_url(url: Optional[str]) -> Optional[str]:
    """
    Convert Next.js optimized URL → direct raw image URL
    Example:
        https://db.pokemongohub.net/_next/image?url=%2Fimages%2Ffoo.webp&w=96&q=75
        → https://db.pokemongohub.net/images/foo.webp
    """
    if not url:
        return None

    # already clean
    if url.startswith("http") and "/_next/image" not in url:
        return url

    # case: next optimized
    if "/_next/image" in url:
        from urllib.parse import urlparse, parse_qs, unquote

        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        raw = qs.get("url", [None])[0]
        if raw:
            raw = unquote(raw).lstrip("/")
            return urljoin(BASE, raw)

    # encoded path
    if url.startswith("%2F") or url.startswith("/%2F"):
        from urllib.parse import unquote
        dec = unquote(url)
        return urljoin(BASE, dec.lstrip("/"))

    # normal relative
    if url.startswith("/"):
        return urljoin(BASE, url)

    return urljoin(BASE, url)
