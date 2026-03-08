"""
NYC Startup Scraper
Sources:
  - Y Combinator (all NYC companies, no tag filter)
  - Techstars NYC
  - ERA (Entrepreneurs Roundtable Accelerator)
  - Betaworks
  - Built In NYC
"""
import asyncio
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


# ── Helpers ────────────────────────────────────────────────────────────────────
def clean(text):
    return re.sub(r'\s+', ' ', text or "").strip()


# ── Y Combinator ───────────────────────────────────────────────────────────────
async def scrape_yc(playwright):
    """
    All YC-backed companies located in New York City (no industry filter).
    Intercepts YC's internal Algolia API calls for structured data,
    falls back to DOM scraping if the API yields nothing.
    """
    companies = []
    api_hits = []

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(user_agent=USER_AGENT)
    page = await context.new_page()

    async def capture_response(response):
        if response.status != 200:
            return
        if "ycombinator.com" not in response.url and "algolia" not in response.url:
            return
        ct = response.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            data = await response.json()
            if isinstance(data, list):
                api_hits.extend(data)
            elif isinstance(data, dict):
                for key in ("hits", "companies", "results", "data"):
                    if key in data and isinstance(data[key], list):
                        api_hits.extend(data[key])
                        break
                # Algolia returns results[0].hits
                if "results" in data and isinstance(data["results"], list):
                    for r in data["results"]:
                        if isinstance(r, dict) and "hits" in r:
                            api_hits.extend(r["hits"])
        except Exception:
            pass

    page.on("response", capture_response)

    # No tags filter — all NYC companies
    await page.goto(
        "https://www.ycombinator.com/companies?location=New+York+City",
        wait_until="networkidle",
        timeout=60000,
    )

    # Scroll down repeatedly to trigger lazy loading
    for _ in range(12):
        await page.keyboard.press("End")
        await asyncio.sleep(1.5)

    if api_hits:
        seen = set()
        for c in api_hits:
            name = clean(c.get("name", ""))
            if not name or name in seen:
                continue
            seen.add(name)
            companies.append({
                "name": name,
                "description": clean(c.get("one_liner") or c.get("short_description", "")),
                "website": c.get("website", ""),
                "url": f"https://www.ycombinator.com/companies/{c.get('slug', '')}",
                "batch": c.get("batch_name") or c.get("batch", ""),
                "stage": "YC Backed",
                "source": "Y Combinator",
                "location": "New York, NY",
            })
    else:
        # DOM fallback
        anchors = await page.query_selector_all("a[href*='/companies/']")
        seen = set()
        for a in anchors:
            try:
                href = await a.get_attribute("href") or ""
                if href in seen or not href.startswith("/companies/"):
                    continue
                seen.add(href)
                text = (await a.inner_text()).strip()
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                if not lines:
                    continue
                companies.append({
                    "name": lines[0],
                    "description": lines[1] if len(lines) > 1 else "",
                    "website": "",
                    "url": f"https://www.ycombinator.com{href}",
                    "batch": "",
                    "stage": "YC Backed",
                    "source": "Y Combinator",
                    "location": "New York, NY",
                })
            except Exception:
                continue

    await browser.close()
    print(f"  YC → {len(companies)} companies")
    return companies


# ── Techstars NYC ──────────────────────────────────────────────────────────────
async def scrape_techstars(playwright):
    """
    Techstars portfolio filtered to NYC programs.
    Uses Playwright because the portfolio page is React-rendered.
    """
    companies = []

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(user_agent=USER_AGENT)
    page = await context.new_page()

    # Capture any JSON API responses from Techstars
    api_data = []

    async def capture(response):
        if response.status != 200:
            return
        if "techstars.com" not in response.url:
            return
        ct = response.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            data = await response.json()
            if isinstance(data, list):
                api_data.extend(data)
            elif isinstance(data, dict):
                for key in ("companies", "results", "data", "items", "hits"):
                    if key in data and isinstance(data[key], list):
                        api_data.extend(data[key])
                        break
        except Exception:
            pass

    page.on("response", capture)

    try:
        await page.goto(
            "https://www.techstars.com/portfolio?location=New+York+City",
            wait_until="networkidle",
            timeout=60000,
        )

        # Scroll to load lazy entries
        for _ in range(10):
            await page.keyboard.press("End")
            await asyncio.sleep(1.5)

        # Try API data first
        if api_data:
            seen = set()
            for c in api_data:
                name = clean(c.get("name") or c.get("companyName", ""))
                if not name or name in seen:
                    continue
                seen.add(name)
                companies.append({
                    "name": name,
                    "description": clean(c.get("description") or c.get("shortDescription", "")),
                    "website": c.get("website") or c.get("url", ""),
                    "url": c.get("website") or c.get("url", ""),
                    "batch": c.get("program") or c.get("cohort", ""),
                    "stage": "Techstars",
                    "source": "Techstars NYC",
                    "location": "New York, NY",
                })
        else:
            # DOM fallback — grab company cards
            await page.wait_for_selector("a[href*='/portfolio/']", timeout=10000)
            cards = await page.query_selector_all("a[href*='/portfolio/']")
            seen = set()
            for card in cards:
                try:
                    href = await card.get_attribute("href") or ""
                    if href in seen:
                        continue
                    seen.add(href)
                    text = clean(await card.inner_text())
                    if not text or len(text) < 2:
                        continue
                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                    name = lines[0] if lines else text
                    desc = lines[1] if len(lines) > 1 else ""
                    full_url = href if href.startswith("http") else f"https://www.techstars.com{href}"
                    companies.append({
                        "name": name,
                        "description": desc,
                        "website": full_url,
                        "url": full_url,
                        "batch": "",
                        "stage": "Techstars",
                        "source": "Techstars NYC",
                        "location": "New York, NY",
                    })
                except Exception:
                    continue

    except Exception as e:
        print(f"  Techstars error: {e}")
    finally:
        await browser.close()

    print(f"  Techstars NYC → {len(companies)} companies")
    return companies


# ── ERA (Entrepreneurs Roundtable Accelerator) ────────────────────────────────
async def scrape_era(playwright):
    """
    ERA is NYC's largest accelerator. Scrapes their portfolio page.
    https://www.eranyc.com/companies
    """
    companies = []

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(user_agent=USER_AGENT)
    page = await context.new_page()

    try:
        await page.goto("https://www.eranyc.com/companies", wait_until="networkidle", timeout=45000)
        await asyncio.sleep(2)

        # Scroll
        for _ in range(6):
            await page.keyboard.press("End")
            await asyncio.sleep(1.5)

        # Try several selectors ERA commonly uses
        cards = await page.query_selector_all(
            "a[href*='/companies/'], .company-card, article.company, "
            "[class*='company'], [class*='portfolio']"
        )

        seen = set()
        for card in cards:
            try:
                # Get name from heading or link text
                name_el = await card.query_selector("h2, h3, h4, [class*='name'], [class*='title']")
                name = clean(await name_el.inner_text()) if name_el else clean(await card.inner_text())
                if not name or len(name) < 2 or name in seen:
                    continue
                seen.add(name)

                desc_el = await card.query_selector("p, [class*='desc'], [class*='tagline']")
                desc = clean(await desc_el.inner_text()) if desc_el else ""

                href = await card.get_attribute("href") or ""
                if not href:
                    link_el = await card.query_selector("a[href]")
                    href = await link_el.get_attribute("href") if link_el else ""
                full_url = href if href.startswith("http") else f"https://www.eranyc.com{href}"

                companies.append({
                    "name": name,
                    "description": desc,
                    "website": full_url,
                    "url": full_url,
                    "batch": "",
                    "stage": "Accelerator",
                    "source": "ERA NYC",
                    "location": "New York, NY",
                })
            except Exception:
                continue

    except Exception as e:
        print(f"  ERA error: {e}")
    finally:
        await browser.close()

    print(f"  ERA NYC → {len(companies)} companies")
    return companies


# ── Betaworks ─────────────────────────────────────────────────────────────────
async def scrape_betaworks(playwright):
    """
    Betaworks is a NYC-based studio/accelerator (bitly, Giphy, etc.)
    https://betaworks.com/companies/
    """
    companies = []

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(user_agent=USER_AGENT)
    page = await context.new_page()

    try:
        await page.goto("https://betaworks.com/companies/", wait_until="networkidle", timeout=45000)
        await asyncio.sleep(2)

        for _ in range(4):
            await page.keyboard.press("End")
            await asyncio.sleep(1)

        cards = await page.query_selector_all("article, .company, [class*='company'], a[href*='/company']")

        seen = set()
        for card in cards:
            try:
                name_el = await card.query_selector("h2, h3, h4, [class*='name']")
                name = clean(await name_el.inner_text()) if name_el else ""
                if not name or name in seen:
                    continue
                seen.add(name)

                desc_el = await card.query_selector("p, [class*='desc']")
                desc = clean(await desc_el.inner_text()) if desc_el else ""

                link_el = await card.query_selector("a[href]")
                href = (await link_el.get_attribute("href")) if link_el else ""
                full_url = href if href.startswith("http") else f"https://betaworks.com{href}"

                companies.append({
                    "name": name,
                    "description": desc,
                    "website": full_url,
                    "url": full_url,
                    "batch": "",
                    "stage": "Betaworks",
                    "source": "Betaworks",
                    "location": "New York, NY",
                })
            except Exception:
                continue

    except Exception as e:
        print(f"  Betaworks error: {e}")
    finally:
        await browser.close()

    print(f"  Betaworks → {len(companies)} companies")
    return companies


# ── Built In NYC ───────────────────────────────────────────────────────────────
async def scrape_builtinnyc(playwright):
    """
    Built In NYC — broader category scrape across tech sectors.
    Uses Playwright to handle JS-rendered content and pagination.
    """
    companies = []

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(user_agent=USER_AGENT)
    page = await context.new_page()

    # Multiple category pages — cast a wide net
    category_urls = [
        "https://www.builtinnyc.com/companies",                          # all companies
        "https://www.builtinnyc.com/companies?category=artificial-intelligence",
        "https://www.builtinnyc.com/companies?category=fintech",
        "https://www.builtinnyc.com/companies?category=healthtech",
        "https://www.builtinnyc.com/companies?category=edtech",
        "https://www.builtinnyc.com/companies?category=ecommerce",
        "https://www.builtinnyc.com/companies?category=saas",
    ]

    seen = set()

    for url in category_urls:
        try:
            await page.goto(url, wait_until="networkidle", timeout=45000)
            await asyncio.sleep(2)

            # Scroll and paginate
            for _ in range(6):
                await page.keyboard.press("End")
                await asyncio.sleep(1.5)

            # Try to click "Load More" if present
            for _ in range(5):
                try:
                    btn = await page.query_selector("button[data-id='load-more'], button:has-text('Load More'), a:has-text('Load More')")
                    if btn:
                        await btn.click()
                        await asyncio.sleep(2)
                    else:
                        break
                except Exception:
                    break

            # Grab company cards
            cards = await page.query_selector_all(
                "article[class*='company'], div[class*='company-card'], "
                "a[href*='/company/'][class*='card'], [data-id*='company']"
            )

            # Fallback: grab all company links
            if not cards:
                cards = await page.query_selector_all("a[href*='/company/']")

            for card in cards:
                try:
                    name_el = await card.query_selector("h2, h3, h4, [class*='name'], [class*='title']")
                    name = clean(await name_el.inner_text()) if name_el else ""
                    if not name or len(name) < 2:
                        name = clean(await card.inner_text())
                        name = name.split('\n')[0].strip()
                    if not name or name.lower() in seen:
                        continue
                    seen.add(name.lower())

                    desc_el = await card.query_selector("p, [class*='desc'], [class*='tagline']")
                    desc = clean(await desc_el.inner_text()) if desc_el else ""

                    href = await card.get_attribute("href") or ""
                    if not href:
                        link_el = await card.query_selector("a[href]")
                        href = await link_el.get_attribute("href") if link_el else ""
                    full_url = href if href.startswith("http") else f"https://www.builtinnyc.com{href}"

                    companies.append({
                        "name": name,
                        "description": desc,
                        "website": full_url,
                        "url": full_url,
                        "batch": "",
                        "stage": "Unknown",
                        "source": "Built In NYC",
                        "location": "New York, NY",
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"  Built In NYC error ({url}): {e}")

    await browser.close()
    print(f"  Built In NYC → {len(companies)} companies")
    return companies


# ── Main ───────────────────────────────────────────────────────────────────────
async def scrape_all():
    print("Scraping NYC startups...\n")

    async with async_playwright() as pw:
        yc, techstars, era, betaworks, builtinnyc = await asyncio.gather(
            scrape_yc(pw),
            scrape_techstars(pw),
            scrape_era(pw),
            scrape_betaworks(pw),
            scrape_builtinnyc(pw),
        )

    all_companies = yc + techstars + era + betaworks + builtinnyc

    # Global deduplicate by normalized name
    seen, unique = set(), []
    for c in all_companies:
        key = re.sub(r'[^a-z0-9]', '', c["name"].lower())
        if key and key not in seen:
            seen.add(key)
            unique.append(c)

    # Sort: YC first, then others
    source_order = {"Y Combinator": 0, "Techstars NYC": 1, "ERA NYC": 2, "Betaworks": 3, "Built In NYC": 4}
    unique.sort(key=lambda c: source_order.get(c["source"], 9))

    print(f"\nTotal unique companies: {len(unique)}")
    by_source = {}
    for c in unique:
        by_source[c["source"]] = by_source.get(c["source"], 0) + 1
    for src, count in sorted(by_source.items(), key=lambda x: source_order.get(x[0], 9)):
        print(f"  {src}: {count}")

    return unique


if __name__ == "__main__":
    companies = asyncio.run(scrape_all())
    with open("startups.json", "w") as f:
        json.dump(companies, f, indent=2)
    print(f"\nSaved to startups.json")
