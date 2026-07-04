import json
import os
import random
import xml.etree.ElementTree as ET

import requests

EKSISEYLER_SITEMAP = "https://eksiseyler.com/sitemap.xml"
DEBE_RSS = "https://politepaul.com/fd/Ruvzo92PKseB.xml"
EVRIMAGACI_RANDOM = "https://evrimagaci.org/rastgele"
KNOWN_LINKS_FILE = "known_eksiseyler.json"
EKSISEYLER_RANDOM_COUNT = 5
EVRIMAGACI_RANDOM_COUNT = 5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _load_known_links():
    if not os.path.exists(KNOWN_LINKS_FILE):
        return []
    with open(KNOWN_LINKS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_known_links(links):
    with open(KNOWN_LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)


def fetch_eksiseyler():
    response = requests.get(EKSISEYLER_SITEMAP, headers=HEADERS, timeout=15)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    all_links = []
    for url in root.findall("sm:url", ns):
        loc = url.findtext("sm:loc", namespaces=ns)
        lastmod = url.findtext("sm:lastmod", namespaces=ns)
        if loc:
            all_links.append({"url": loc.strip(), "lastmod": lastmod})

    known = set(_load_known_links())
    current_urls = {item["url"] for item in all_links}

    new_links = [item for item in all_links if item["url"] not in known]
    random_links = random.sample(all_links, min(EKSISEYLER_RANDOM_COUNT, len(all_links)))

    _save_known_links(sorted(current_urls))

    return {"random": random_links, "new": new_links}


def fetch_debe():
    response = requests.get(DEBE_RSS, headers=HEADERS, timeout=15)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items = []
    for item in root.findall(".//item"):
        title = item.findtext("title")
        link = item.findtext("link")
        if title and link:
            items.append({"title": title.strip(), "url": link.strip()})

    return items


def fetch_evrimagaci():
    session = requests.Session()
    session.headers.update(HEADERS)

    collected = []
    seen = set()
    attempts = 0
    max_attempts = EVRIMAGACI_RANDOM_COUNT * 3

    while len(collected) < EVRIMAGACI_RANDOM_COUNT and attempts < max_attempts:
        attempts += 1
        try:
            response = session.get(
                EVRIMAGACI_RANDOM, allow_redirects=True, timeout=10
            )
            final_url = response.url
            if final_url != EVRIMAGACI_RANDOM and final_url not in seen:
                seen.add(final_url)
                collected.append(final_url)
        except requests.RequestException:
            continue

    return collected


def collect_all():
    eksiseyler = fetch_eksiseyler()
    debe = fetch_debe()
    evrimagaci = fetch_evrimagaci()

    return {
        "eksiseyler_random": eksiseyler["random"],
        "eksiseyler_new": eksiseyler["new"],
        "debe": debe,
        "evrimagaci": evrimagaci,
    }
