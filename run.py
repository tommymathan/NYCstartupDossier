"""
NYC AI Startup Dossier — main runner

Usage:
  python run.py              # scrape + generate map
  python run.py --cache      # skip scraping, regenerate map from startups.json
  python run.py --scrape-only  # scrape and save, no map
"""
import asyncio
import json
import os
import subprocess
import sys


def install_playwright_browsers():
    """Install Chromium if not already installed."""
    result = subprocess.run(
        ["python3", "-m", "playwright", "install", "chromium"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Warning: could not install Playwright browsers automatically.")
        print(result.stderr)


async def main():
    from scraper import scrape_all
    from map_gen import generate_map

    data_file = "startups.json"
    map_file = "nyc_ai_startups_map.html"
    use_cache = "--cache" in sys.argv
    scrape_only = "--scrape-only" in sys.argv

    # ── Step 1: Scrape ────────────────────────────────────────────────────────
    if use_cache and os.path.exists(data_file):
        print(f"Using cached data from {data_file}")
        with open(data_file) as f:
            companies = json.load(f)
        print(f"Loaded {len(companies)} companies.")
    else:
        companies = await scrape_all()
        with open(data_file, "w") as f:
            json.dump(companies, f, indent=2)
        print(f"\nSaved {len(companies)} companies → {data_file}")

    if scrape_only:
        return

    # ── Step 2: Generate map ──────────────────────────────────────────────────
    print()
    generate_map(data_file, map_file)

    print(f"\n✅ Done!")
    print(f"   Data:  {data_file}")
    print(f"   Map:   {map_file}")
    print(f"\nOpening map in browser…")
    subprocess.run(["open", map_file], check=False)


if __name__ == "__main__":
    # Make sure Playwright has its browser binaries
    if "--no-install" not in sys.argv:
        install_playwright_browsers()
    asyncio.run(main())
