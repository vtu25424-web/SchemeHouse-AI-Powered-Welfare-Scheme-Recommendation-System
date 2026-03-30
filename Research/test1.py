# myscheme_scraper.py
# pip install playwright beautifulsoup4 pandas
# playwright install chromium

import json
import re
import csv
from pathlib import Path
from urllib.parse import urljoin, quote

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE = "https://www.myscheme.gov.in"

# Keywords that are useful for college-student related discovery
SEARCH_TAGS = [
    "student",
    "students",
    "college",
    "education",
    "scholarship",
    "youth",
    "technical education",
]

OUT_DIR = Path("myscheme_output")
OUT_DIR.mkdir(exist_ok=True)


def clean_text(value: str) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value)
    return value.strip()

def extract_block_lines(container):
    if not container:
        return ""
    items = []
    for li in container.select("li"):
        txt = clean_text(li.get_text(" ", strip=True))
        if txt:
            items.append(txt)
    return "\n".join(f"- {x}" for x in items)


def extract_scheme_links_from_html(html: str) -> list[str]:
    """
    Pull every /schemes/<slug> link from a rendered page.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.select('a[href*="/schemes/"]'):
        href = a.get("href", "").strip()
        if not href:
            continue
        full = urljoin(BASE, href)
        if "/schemes/" in full:
            links.add(full)

    return sorted(links)


def extract_section_by_heading(soup: BeautifulSoup, heading_keywords: list[str]) -> str:
    """
    Find the first heading containing one of the keywords and collect text
    until the next heading.
    """
    headings = soup.find_all(re.compile(r"^h[1-6]$"))

    for h in headings:
        h_text = clean_text(h.get_text(" ", strip=True)).lower()
        if any(k in h_text for k in heading_keywords):
            # Try to find <ul> or <ol> in the next siblings or inside the next <div>
            node = h.find_next_sibling()
            while node is not None and not re.match(r"^h[1-6]$", getattr(node, "name", "") or ""):
                # If node is a <ul> or <ol>, extract all list items
                if getattr(node, "name", None) in ["ul", "ol"]:
                    items = [clean_text(li.get_text(" ", strip=True)) for li in node.find_all("li")]
                    if items:
                        return "\n".join(items).strip()
                # If node is a <div>, look for <ul>/<ol> inside it
                if getattr(node, "name", None) == "div":
                    ul = node.find("ul")
                    ol = node.find("ol")
                    if ul:
                        items = [clean_text(li.get_text(" ", strip=True)) for li in ul.find_all("li")]
                        if items:
                            return "\n".join(items).strip()
                    if ol:
                        items = [clean_text(li.get_text(" ", strip=True)) for li in ol.find_all("li")]
                        if items:
                            return "\n".join(items).strip()
                # Otherwise, just collect text as before
                txt = clean_text(node.get_text(" ", strip=True)) if getattr(node, "get_text", None) else ""
                if txt:
                    return txt
                node = node.find_next_sibling()
            # If nothing found, fallback to old logic (collect all text until next heading)
            chunks = []
            node = h.find_next_sibling()
            while node is not None and not re.match(r"^h[1-6]$", getattr(node, "name", "") or ""):
                txt = clean_text(node.get_text(" ", strip=True)) if getattr(node, "get_text", None) else ""
                if txt:
                    chunks.append(txt)
                node = node.find_next_sibling()
            return "\n".join(chunks).strip()

    return ""


def extract_scheme_data(page) -> dict:
    """
    Extract title, description, sections, and likely application link
    from a scheme detail page.
    """
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    title = clean_text(h1.get_text(" ", strip=True)) if h1 else ""

    canonical = soup.find("link", attrs={"rel": "canonical"})
    url = canonical.get("href", page.url) if canonical else page.url

    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = clean_text(meta_desc.get("content", "")) if meta_desc else ""

    # Direct extraction from known section IDs
    eligibility_container = soup.select_one("#eligibility")
    benefits_container = soup.select_one("#benefits, #benefit")
    docs_container = soup.select_one("#documents, #required-documents, #document")
    apply_container = soup.select_one("#how-to-apply, #apply, #application-process")

    eligibility = extract_block_lines(eligibility_container)
    benefits = extract_block_lines(benefits_container)
    documents = extract_block_lines(docs_container)
    how_to_apply = extract_block_lines(apply_container)

    # Fallback: if section IDs are missing, use heading-based extraction
    if not eligibility:
        for heading in soup.find_all(re.compile(r"^h[1-6]$")):
            if "eligibility" in clean_text(heading.get_text(" ", strip=True)).lower():
                parent = heading.find_parent()
                if parent:
                    items = [clean_text(li.get_text(" ", strip=True)) for li in parent.select("li")]
                    if items:
                        eligibility = "\n".join(f"- {x}" for x in items)
                    else:
                        eligibility = clean_text(parent.get_text(" ", strip=True))
                break

    # Find application link
    application_link = ""
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        txt = clean_text(a.get_text(" ", strip=True)).lower()
        if not href:
            continue
        full = urljoin(BASE, href)

        if any(k in txt for k in ["apply", "application", "register", "submit"]) or \
           any(k in href.lower() for k in ["apply", "application", "register", "submit"]):
            application_link = full
            break

    return {
        "title": title,
        "url": url,
        "description": description,
        "eligibility": eligibility or "",
        "benefits": benefits or "",
        "how_to_apply": how_to_apply or "",
        "documents": documents or "",
        "application_link": application_link or "",
    }


def crawl_search_pages(page) -> set[str]:
    """
    Visit a set of likely search/tag pages and collect scheme URLs.
    """
    scheme_urls = set()

    # Main entry points visible on the site
    seed_urls = [
        f"{BASE}/find-scheme",
        f"{BASE}/search?tag=Student",
        f"{BASE}/search?tag=Students",
        f"{BASE}/search?tag=College",
        f"{BASE}/search?tag=Education",
        f"{BASE}/search?tag=Scholarship",
        f"{BASE}/search?tag=Youth",
    ]

    for url in seed_urls:
        try:
            page.goto(url, wait_until="networkidle", timeout=45000)
            scheme_urls.update(extract_scheme_links_from_html(page.content()))
        except PlaywrightTimeoutError:
            # Keep going even if a page is slow
            try:
                scheme_urls.update(extract_scheme_links_from_html(page.content()))
            except Exception:
                pass
        except Exception:
            pass

    return scheme_urls


def main():
    records = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1200})
        page = context.new_page()

        # Step 1: collect scheme links
        scheme_urls = crawl_search_pages(page)
        print(f"Found {len(scheme_urls)} unique scheme links.")

        # Step 2: visit each scheme page and extract details
        for i, scheme_url in enumerate(sorted(scheme_urls), 1):
            if scheme_url in seen:
                continue
            seen.add(scheme_url)

            try:
                page.goto(scheme_url, wait_until="networkidle", timeout=45000)
                data = extract_scheme_data(page)

                # Keep only meaningful records
                if data["title"] or data["description"] or data["eligibility"] or data["benefits"]:
                    records.append(data)
                    print(f"[{i}/{len(scheme_urls)}] OK  {data['title'] or scheme_url}")
                else:
                    print(f"[{i}/{len(scheme_urls)}] SKIP {scheme_url} (empty page content)")
            except Exception as e:
                print(f"[{i}/{len(scheme_urls)}] ERR {scheme_url} -> {e}")

        browser.close()

    # Save JSON
    json_path = OUT_DIR / "myscheme_schemes.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # Save CSV
    csv_path = OUT_DIR / "myscheme_schemes.csv"
    df = pd.DataFrame(records)
    if not df.empty:
        df.drop(columns=["all_links"], inplace=True, errors="ignore")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(columns=[
            "title", "url", "description", "eligibility", "benefits",
            "how_to_apply", "documents", "application_link"
        ]).to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"\nSaved JSON: {json_path}")
    print(f"Saved CSV : {csv_path}")
    print(f"Total records: {len(records)}")


if __name__ == "__main__":
    main()