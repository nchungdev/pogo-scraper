from src.pipelines.helpers import load_config, run_scraper_by_name


def run_weekly_pipeline():
    print("=== WEEKLY PIPELINE STARTED ===")
    cfg = load_config()

    for name, entry in cfg["scrapers"].items():
        if entry.get("enabled") and entry.get("pipeline") == "weekly":
            run_scraper_by_name(name, cfg)

    print("=== WEEKLY PIPELINE DONE ===")


if __name__ == "__main__":
    run_weekly_pipeline()
