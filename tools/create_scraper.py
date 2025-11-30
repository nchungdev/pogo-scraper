#!/usr/bin/env python3
import argparse
import os
from textwrap import dedent

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRAPERS_ROOT = os.path.join(PROJECT_ROOT, "src", "scrapers")


def snake_case(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_")


def pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in snake_case(name).split("_"))


def create_folder(path: str):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✓ Created folder: {path}")


def write_file(path: str, content: str):
    create_folder(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✓ Generated file: {path}")


def ensure_init(path: str):
    init_path = os.path.join(path, "__init__.py")
    if not os.path.exists(init_path):
        write_file(init_path, "# auto-generated\n")


def generate_scraper(category: str, name: str, title: str):
    cat_snake = snake_case(category)
    name_snake = snake_case(name)
    class_name = pascal_case(name) + "Scraper"

    # Folder paths
    category_path = os.path.join(SCRAPERS_ROOT, cat_snake)
    parser_path = os.path.join(category_path, "parsers")

    create_folder(category_path)
    create_folder(parser_path)
    ensure_init(category_path)
    ensure_init(parser_path)

    # -------------------------
    # 1) Scraper file
    # -------------------------
    scraper_file = os.path.join(category_path, f"{name_snake}_scraper.py")

    scraper_code = dedent(f"""
    from src.base.base_scraper import BaseScraper
    from .parsers.{name_snake}_parser import parse_{name_snake}

    class {class_name}(BaseScraper):
        \"\"\"Scraper: {title}\"\"\"

        def parse(self, soup):
            # NOTE: 'soup' is BeautifulSoup object
            # You should edit parse logic inside parser file.
            return parse_{name_snake}(soup)
    """)

    write_file(scraper_file, scraper_code)

    # -------------------------
    # 2) Parser file
    # -------------------------
    parser_file = os.path.join(parser_path, f"{name_snake}_parser.py")

    parser_code = dedent(f"""
    # Parser for {title}

    def parse_{name_snake}(soup):
        \"\"\"
        Return a Python dict or list.
        You must implement actual parsing logic.
        \"\"\"
        return {{
            "title": "{title}",
            "status": "parser_not_implemented",
        }}
    """)

    write_file(parser_file, parser_code)

    # -------------------------
    # 3) Import aggregator update
    # -------------------------
    init_path = os.path.join(category_path, "__init__.py")

    with open(init_path, "a", encoding="utf-8") as f:
        f.write(f"from .{name_snake}_scraper import {class_name}\n")

    print(f"✓ Updated __init__.py for: {category}")

    print("\n🎉 Done! Files created:")
    print(f"  - {scraper_file}")
    print(f"  - {parser_file}")
    print("")
    print("⭐ Note:")
    print("  Add this scraper to your pipeline manually:")
    print(f"    from src.scrapers.{cat_snake} import {class_name}")
    print("")


def main():
    parser = argparse.ArgumentParser(description="Create scraper boilerplate")
    parser.add_argument("category", help="scraper category (e.g. pokemon, moves, raids)")
    parser.add_argument("name", help="scraper name (e.g. type_chart, fast_moves_pve)")
    parser.add_argument("--title", default="Untitled Scraper", help="Human readable title")

    args = parser.parse_args()
    generate_scraper(args.category, args.name, args.title)


if __name__ == "__main__":
    main()
