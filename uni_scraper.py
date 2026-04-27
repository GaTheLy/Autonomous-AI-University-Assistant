"""
Robust web scraper for Chinese university websites using Playwright (Async version).

Handles JS-rendered pages, Chinese text encoding, bot protection,
and async content loading — problems that basic requests-based scrapers can't handle.
Optimized for Jupyter notebooks which run in an asyncio loop.

Usage:
    from scraper import fetch_website_contents, fetch_website_links, fetch_multiple_pages

    # Single page
    text = await fetch_website_contents("https://www.tsinghua.edu.cn/en/")

    # Extract links
    links = await fetch_website_links("https://www.tsinghua.edu.cn/en/")

    # Multiple pages combined
    urls = ["https://uni.edu.cn/admissions", "https://uni.edu.cn/scholarships"]
    combined = await fetch_multiple_pages(urls)
"""

import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from urllib.parse import urljoin, urlparse


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",  # evade bot detection
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

DEFAULT_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}

# Tags to strip from extracted content
NOISE_TAGS = ["script", "style", "img", "input", "svg", "iframe", "noscript",
              "nav", "footer", "header"]

# CSS selectors for common boilerplate regions to remove
NOISE_SELECTORS = [
    "nav", "footer", "header",
    "[role='navigation']", "[role='banner']", "[role='contentinfo']",
    ".cookie-banner", ".cookie-notice", "#cookie-consent",
    ".social-share", ".share-buttons",
    ".breadcrumb", ".pagination",
    ".sidebar", "#sidebar",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _launch_browser(playwright):
    """Launch a headless Chromium browser with stealth settings."""
    browser = await playwright.chromium.launch(
        headless=True,
        args=BROWSER_ARGS,
    )
    return browser


async def _new_context(browser):
    """Create a browser context that mimics a real user."""
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        extra_http_headers=DEFAULT_HEADERS,
    )
    return context


def _extract_text(html: str, max_chars: int = 5000) -> str:
    """
    Parse rendered HTML with BeautifulSoup and return clean text.
    Strips navigation, scripts, styles, and other noise.
    """
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"

    if not soup.body:
        return f"{title}\n\n(No body content found)"

    # Remove noisy tags
    for tag_name in NOISE_TAGS:
        for tag in soup.body.find_all(tag_name):
            tag.decompose()

    # Remove noisy selectors (cookie banners, navs, footers, etc.)
    for selector in NOISE_SELECTORS:
        for element in soup.body.select(selector):
            element.decompose()

    # Remove elements that look like menus (lists of short links)
    for ul in soup.body.find_all(["ul", "ol"]):
        items = ul.find_all("li")
        if items and all(len(li.get_text(strip=True)) < 30 for li in items):
            # Likely a nav menu — all items are short
            link_count = len(ul.find_all("a"))
            if link_count >= 3 and link_count / max(len(items), 1) > 0.6:
                ul.decompose()

    # Extract tables separately for better formatting
    tables_text = []
    for table in soup.body.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if any(cells):
                rows.append(" | ".join(cells))
        if rows:
            tables_text.append("\n".join(rows))
        table.decompose()  # remove so it doesn't duplicate in main text

    # Get remaining body text
    body_text = soup.body.get_text(separator="\n", strip=True)

    # Clean up: remove blank lines and deduplicate short repeated lines (nav artifacts)
    lines = []
    seen_short = set()
    for line in body_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Deduplicate short lines (< 40 chars) — nav items often appear 2-3 times
        if len(stripped) < 40:
            if stripped in seen_short:
                continue
            seen_short.add(stripped)
        lines.append(stripped)
    cleaned = "\n".join(lines)

    # Append extracted tables
    if tables_text:
        cleaned += "\n\n--- TABLES ---\n" + "\n\n".join(tables_text)

    return (title + "\n\n" + cleaned)[:max_chars]


def _extract_links(html: str, base_url: str) -> list[str]:
    """Extract all links from the page, resolving relative URLs to absolute."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        absolute = urljoin(base_url, href)
        links.append(absolute)
    # Deduplicate while preserving order
    return list(dict.fromkeys(links))


async def _load_page(page, url: str, timeout: int):
    """Navigate to URL and wait for content to settle."""
    try:
        # Many Chinese university websites contain blocked external scripts (like Google Fonts)
        # that prevent 'domcontentloaded' from fully triggering. We catch the timeout and parse anyway.
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    except PlaywrightTimeout:
        pass
        
    try:
        await page.wait_for_load_state("networkidle", timeout=min(timeout, 10000))
    except PlaywrightTimeout:
        pass  # Some Chinese sites never fully settle; that's OK

    # Extra wait for lazy-loaded content
    await page.wait_for_timeout(1500)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_website_contents(url: str, max_chars: int = 5000, timeout: int = 30000) -> str:
    """
    Fetch and extract clean text content from a URL using a headless browser.
    Must be awaited.
    """
    try:
        async with async_playwright() as pw:
            browser = await _launch_browser(pw)
            context = await _new_context(browser)
            page = await context.new_page()

            await _load_page(page, url, timeout)
            html = await page.content()

            await browser.close()

        return _extract_text(html, max_chars)

    except PlaywrightTimeout:
        return f"Error: Timed out loading {url} (waited {timeout}ms)"
    except Exception as e:
        return f"Error scraping {url}: {type(e).__name__}: {e}"


async def fetch_website_links(url: str, timeout: int = 30000) -> list[str]:
    """
    Fetch all links from a URL using a headless browser.
    Must be awaited.
    """
    try:
        async with async_playwright() as pw:
            browser = await _launch_browser(pw)
            context = await _new_context(browser)
            page = await context.new_page()

            await _load_page(page, url, timeout)
            html = await page.content()

            await browser.close()

        return _extract_links(html, url)

    except PlaywrightTimeout as e:
        import traceback
        print(f"Warning: Timed out loading {url}")
        traceback.print_exc()
        return []
    except Exception as e:
        import traceback
        print(f"Error fetching links from {url}: {type(e).__name__}: {e}")
        traceback.print_exc()
        return []


async def fetch_multiple_pages(
    urls: list[str],
    max_chars: int = 5000,
    timeout: int = 30000,
) -> str:
    """
    Scrape multiple pages and concatenate their content.
    Reuses a single browser instance for efficiency.
    Must be awaited.
    """
    results = []

    try:
        async with async_playwright() as pw:
            browser = await _launch_browser(pw)
            context = await _new_context(browser)

            for url in urls:
                page = await context.new_page()
                try:
                    await _load_page(page, url, timeout)
                    html = await page.content()
                    text = _extract_text(html, max_chars)
                    results.append(f"=== SOURCE: {url} ===\n\n{text}")
                except PlaywrightTimeout:
                    results.append(f"=== SOURCE: {url} ===\n\nError: Timed out")
                except Exception as e:
                    results.append(f"=== SOURCE: {url} ===\n\nError: {e}")
                finally:
                    await page.close()

            await browser.close()

    except Exception as e:
        results.append(f"Browser launch error: {e}")

    return "\n\n" + "\n\n".join(results)
