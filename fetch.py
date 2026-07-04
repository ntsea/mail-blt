import json
import random
import xml.etree.ElementTree as ET

import requests

EKSISEYLER_LINKS_FILE = "eksiseyler_links.json"
DEBE_RSS = "https://politepaul.com/fd/Ruvzo92PKseB.xml"
EVRIMAGACI_RANDOM = "https://evrimagaci.org/rastgele"
EKSISEYLER_RANDOM_COUNT = 5
EVRIMAGACI_RANDOM_COUNT = 5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_eksiseyler():
    with open(EKSISEYLER_LINKS_FILE, encoding="utf-8") as f:
        all_links = json.load(f)

    random_links = random.sample(all_links, min(EKSISEYLER_RANDOM_COUNT, len(all_links)))
    return {"random": random_links}


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
    try:
        eksiseyler = fetch_eksiseyler()
    except Exception:
        eksiseyler = {"random": [], "error": True}

    debe = fetch_debe()
    evrimagaci = fetch_evrimagaci()

    return {
        "eksiseyler_random": eksiseyler["random"],
        "eksiseyler_error": eksiseyler.get("error", False),
        "debe": debe,
        "evrimagaci": evrimagaci,
    }
