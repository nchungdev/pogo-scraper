# Pokémon GO Data Scraper

[![Hourly Scraper](https://github.com/nchungdev/pogo-scraper/actions/workflows/scrape_hourly.yml/badge.svg)](https://github.com/nchungdev/pogo-scraper/actions/workflows/scrape_hourly.yml)<br>
[![Daily Scraper](https://github.com/nchungdev/pogo-scraper/actions/workflows/scrape_daily.yml/badge.svg)](https://github.com/nchungdev/pogo-scraper/actions/workflows/scrape_daily.yml)<br>
[![Weekly Scraper](https://github.com/nchungdev/pogo-scraper/actions/workflows/scrape_weekly.yml/badge.svg)](https://github.com/nchungdev/pogo-scraper/actions/workflows/scrape_weekly.yml)<br>
[![Monthly Scraper](https://github.com/nchungdev/pogo-scraper/actions/workflows/scrape_monthly.yml/badge.svg)](https://github.com/nchungdev/pogo-scraper/actions/workflows/scrape_monthly.yml)<br>
![Last Updated](https://img.shields.io/github/last-commit/nchungdev/pogo-scraper/data)

A fully automated scraping system designed to fetch, cache, and publish structured Pokémon GO game data.  
This project provides high-quality datasets updated on *hourly, daily, weekly, and monthly* schedules using GitHub Actions.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Scraped Data Sources](#scraped-data-sources)
- [Automation Schedules](#automation-schedules)
- [Repository Layout](#repository-layout)
- [Running Locally](#running-locally)
- [Data Output](#data-output)
- [Extending the System](#extending-the-system)
- [License](#license)

---

## 📖 Overview

This repository hosts a modular, scalable scraper system for collecting structured Pokémon GO data from multiple public sources such as:

- Pokémon GO Hub
- LeekDuck
- RaidNow
- PokéAPI

The scraper outputs standardized JSON files which are automatically committed to a dedicated **data** branch and can be used as free static JSON APIs for apps or research.

---

## ✨ Features

- **Automated multi-frequency scraping**
    - Hourly updates
    - Daily updates
    - Weekly updates
    - Monthly updates
- **HTML caching system**
    - Metadata timestamping
    - Cache expiry rules
    - GitHub Action HTML restoration
- **Fully modular scraper architecture**
    - Each scraper inherits from `BaseScraper`
    - Each group of scrapers has its own pipeline
- **Resilient**
    - Retries, delays, timeouts
    - Graceful fallback even when scraping partially fails
- **Data stored in a separate branch**
    - Allows clean separation between code and generated data
- **Extensible**
    - Add new scrapers or pipelines easily

---

## 🎯 Scraped Data Sources

| Category | Source | Frequency |
|---------|--------|-----------|
| Type Chart | Pokémon GO Hub | daily |
| Pokémon Detail | Pokémon GO Hub | weekly/monthly |
| Moves (PvE/PvP) | Pokémon GO Hub | weekly |
| Raids / Eggs / Rocket | LeekDuck | hourly |
| RaidNow Feed | RaidNow | hourly |
| Pokémon Species List | PokéAPI | cached / as needed |

---

## ⏱ Automation Schedules

Four workflows live in `.github/workflows/`:

| Workflow | Cron | Purpose |
|----------|------|---------|
| `scrape_hourly.yml` | Every hour | Raids, Eggs, Research, Rocket, RaidNow |
| `scrape_daily.yml` | Every 24h | Type Chart, Moves |
| `scrape_weekly.yml` | Weekly | Pokémon Detail (partial) |
| `scrape_monthly.yml` | Monthly | Full Pokémon Dataset rebuild |

All workflows push JSON + HTML cache to the `data` branch.

---

## 🗂 Repository Layout

```
project/
│
├── src/
│   ├── base/
│   │   ├── base_scraper.py
│   │   ├── html_cache.py
│   │   └── playwright_fetcher.py
│   │
│   ├── common/
│   │   ├── utils.py
│   │   ├── normalize.py
│   │   ├── url_utils.py
│   │   └── text_utils.py
│   │
│   ├── pipelines/
│   │   ├── hourly_pipeline.py
│   │   ├── daily_pipeline.py
│   │   ├── weekly_pipeline.py
│   │   └── monthly_pipeline.py
│   │
│   ├── scrapers/
│   │   ├── pokemon/
│   │   ├── moves/
│   │   ├── raids/
│   │   ├── types/
│   │   └── events/
│   │
│   └── main.py
│
├── output/ (local only, gitignored)
│   ├── html/
│   └── json/
│
├── data branch (GitHub only)
│   ├── html/
│   └── json/
│
└── README.md
```

---

## 🧪 Running Locally

### 1. Clone & setup:

```sh
git clone https://github.com/nchungdev/pogo-scraper
cd pogo-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium
```

### 2. Run the entire pipeline:

```sh
python -m src.main
```

### 3. Run a specific mode:

```sh
python -m src.main --mode hourly
python -m src.main --mode daily
python -m src.main --mode weekly
python -m src.main --mode monthly
```

---

## 📤 Data Output

All generated JSON & cached HTML are committed to the **data branch**, e.g.:

```
https://raw.githubusercontent.com/nchungdev/pogo-scraper/data/json/raid_bosses.json
https://raw.githubusercontent.com/nchungdev/pogo-scraper/data/json/type_chart.json
https://raw.githubusercontent.com/nchungdev/pogo-scraper/data/json/species_list.json
```

You can use them as free CDN-served JSON endpoints.

---

## ➕ Extending the System

To create a new scraper:

```sh
python tools/create_scraper.py category name --title "My Scraper"
```

The generator produces:

- Scraper class
- Parser folder
- Pipeline integration
- Imports in `__init__.py`

---

## 📄 License

Distributed under the MIT License.  
Pokémon assets belong to The Pokémon Company / Niantic – this project is not affiliated with them.