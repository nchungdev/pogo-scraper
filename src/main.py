import json
import os
import sys
from typing import Any

from src import scrapers

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ----------------------------------------------------------
# Load config
# ----------------------------------------------------------
def load_config() -> dict[str, Any]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    with open(config_path, "r") as f:
        return json.load(f)


# ----------------------------------------------------------
# Schedule control based on config.json
# ----------------------------------------------------------
def get_local_hour_utc7() -> int:
    """Get local hour by converting UTC → UTC+7."""
    utc_hour = int(os.popen("date -u +%H").read().strip())
    return (utc_hour + 7) % 24


def should_run_scraper(name: str, settings: dict[str, Any]) -> bool:
    schedule = settings.get("schedule", {})
    interval = schedule.get("interval_minutes")

    # 👇 Nếu không có schedule → cho chạy
    if interval is None:
        return True

    # 👇 Nếu scraper có active_hours (chỉ dùng cho RaidNow)
    active_hours = schedule.get("active_hours")
    if active_hours:
        local_h = get_local_hour_utc7()
        start_h, end_h = active_hours
        if start_h <= local_h <= end_h:
            print(f"[RUN] {name}: inside active hours {start_h}-{end_h}", flush=True)
            return True
        else:
            print(f"[SKIP] {name}: outside active hours {start_h}-{end_h}", flush=True)
            return False

    # 👇 Không có active_hours → luôn chạy
    return True

# ----------------------------------------------------------
# Run a single scraper class
# ----------------------------------------------------------
def run_scraper(scraper_info: dict[str, Any]) -> str:
    scraper_class_name = scraper_info["class_name"]
    config = scraper_info["config"]

    try:
        print(f"--- Running {scraper_class_name} ---", flush=True)
        scraper_class = getattr(scrapers, scraper_class_name)

        scraper_args: dict[str, Any] = {
            "url": config["scrapers"][scraper_class_name]["url"],
            "file_name": config["scrapers"][scraper_class_name]["file_name"],
            "scraper_settings": config["scraper_settings"],
        }

        # EventScraper special arguments
        if scraper_class_name == "EventScraper":
            scraper_args["check_existing_events"] = config["scrapers"][
                "EventScraper"
            ].get("check_existing", False)
            scraper_args["github_user"] = config["github"]["user"]
            scraper_args["github_repo"] = config["github"]["repo"]

        scraper_instance = scraper_class(**scraper_args)
        scraper_instance.run()
        return f"Successfully ran {scraper_class_name}"

    except Exception as e:
        return f"✗ ERROR running {scraper_class_name}: {e}"


# ----------------------------------------------------------
# Main workflow
# ----------------------------------------------------------
def main():
    print("=== Starting Leak Duck Scrapers ===", flush=True)
    config = load_config()
    print("Configuration loaded", flush=True)

    # ------------------------------------------
    # Determine which scrapers to run
    # ------------------------------------------
    scrapers_to_run: list[dict[str, Any]] = []

    for name, settings in config["scrapers"].items():
        if not settings.get("enabled", False):
            continue

        # NEW: Skip based on schedule rules
        if not should_run_scraper(name, settings):
            continue

        scrapers_to_run.append({"class_name": name, "config": config})

    # ------------------------------------------
    # Execute selected scrapers
    # ------------------------------------------
    for scraper in scrapers_to_run:
        result = run_scraper(scraper)
        print(result, flush=True)

    print("=== All scrapers finished ===", flush=True)


if __name__ == "__main__":
    main()