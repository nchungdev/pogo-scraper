from src.pipelines.helpers import load_config, run_scraper_by_name


def run_hourly_pipeline():
    print("=== HOURLY PIPELINE STARTED ===")
    cfg = load_config()

    for name, entry in cfg["scrapers"].items():
        if entry.get("enabled") and entry.get("pipeline") == "hourly":
            run_scraper_by_name(name, cfg)

    print("=== HOURLY PIPELINE DONE ===")


if __name__ == "__main__":
    run_hourly_pipeline()