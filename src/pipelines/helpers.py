import json
import os
from typing import Dict, Any

from src import scrapers

def load_config() -> Dict[str, Any]:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config.json"), "r") as f:
        return json.load(f)


def run_scraper_by_name(name: str, cfg: Dict[str, Any]):
    cls = getattr(scrapers, name)
    s_cfg = cfg["scrapers"][name]
    inst = cls(
        scraper=s_cfg,
        scraper_settings=cfg["scraper_settings"]
    )
    print(f"→ Running {name}")
    inst.run()
