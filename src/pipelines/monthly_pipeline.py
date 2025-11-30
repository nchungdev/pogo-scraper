from src.pipelines.helpers import load_config, run_scraper_by_name


def run_monthly_pipeline():
    print("=== MONTHLY PIPELINE STARTED ===")
    cfg = load_config()

    for name, entry in cfg["scrapers"].items():
        if entry.get("enabled") and entry.get("pipeline") == "monthly":
            run_scraper_by_name(name, cfg)

    print("=== MONTHLY PIPELINE DONE ===")


if __name__ == "__main__":
    run_monthly_pipeline()
