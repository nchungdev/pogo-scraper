import sys

from src.pipelines.daily_pipeline import run_daily_pipeline
from src.pipelines.hourly_pipeline import run_hourly_pipeline
from src.pipelines.monthly_pipeline import run_monthly_pipeline
from src.pipelines.weekly_pipeline import run_weekly_pipeline


def main():
    if len(sys.argv) <= 1:
        print("No args → default = all pipelines")
        run_hourly_pipeline()
        run_daily_pipeline()
        run_weekly_pipeline()
        run_monthly_pipeline()
        return

    mode = sys.argv[1].lower()

    if mode == "hourly":
        run_hourly_pipeline()
    elif mode == "daily":
        run_daily_pipeline()
    elif mode == "weekly":
        run_weekly_pipeline()
    elif mode == "monthly":
        run_monthly_pipeline()
    else:
        print("Unknown mode → running ALL")
        run_hourly_pipeline()
        run_daily_pipeline()
        run_weekly_pipeline()
        run_monthly_pipeline()


if __name__ == "__main__":
    main()