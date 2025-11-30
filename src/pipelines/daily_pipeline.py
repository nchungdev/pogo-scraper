from src.pipelines.helpers import load_config, run_scraper_by_name


def run_daily_pipeline():
    print("=== DAILY PIPELINE STARTED ===")
    cfg = load_config()

    for name, entry in cfg["scrapers"].items():
        if entry.get("enabled") and entry.get("pipeline") == "daily":
            run_scraper_by_name(name, cfg)

    print("=== DAILY PIPELINE DONE ===")


if __name__ == "__main__":
    run_daily_pipeline()
