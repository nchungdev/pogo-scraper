import re
from typing import Optional


def extract_number(text: str):
    m = re.search(r"\d+", text)
    return int(m.group(0)) if m else None


def clean_cp_text(cp_text: Optional[str]) -> Optional[str]:
    """
    Clean CP-like text while preserving ranges and separators.

    Examples:
      "1260 CP" -> "1260"
      "590 CP - 637 CP" -> "590 - 637"
      "1260CP" -> "1260"
      "Level 50, 15/15/15 IVs" -> "Level 50, 15/15/15 IVs"  (if passed non-cp text it will be returned mostly intact)
    """
    if not cp_text:
        return None

    txt = str(cp_text)

    # 1) remove query params or Next.js wrappers if accidentally passed full URL fragment (defensive)
    #    not required here but harmless: remove trailing "CP" tokens first
    # remove standalone 'CP' words (case-insensitive)
    txt = re.sub(r"\bCP\b", "", txt, flags=re.I)

    # remove cases like "590CP" or "1260CP" (number immediately followed by CP)
    txt = re.sub(r"(\d)CP\b", r"\1", txt, flags=re.I)

    # remove extra commas and multiple spaces
    txt = re.sub(r"[,\u00A0]+", " ", txt)

    # normalize whitespace
    txt = re.sub(r"\s{2,}", " ", txt).strip()

    # remove stray separators at ends
    txt = txt.strip(" -–—,").strip()

    # If result is purely numeric with trailing non-digit chars, trim non-digits
    # but preserve ranges like "590 - 637" or "590-637"
    # collapse multiple dash variants to simple " - "
    txt = re.sub(r"[–—]+", "-", txt)  # normalize dash chars
    txt = re.sub(r"\s*-\s*", " - ", txt)  # ensure spaced dash

    # final trim
    txt = txt.strip()

    return txt if txt != "" else None
