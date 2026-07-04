import json
import xml.etree.ElementTree as ET

import requests

SITEMAP_URL = "https://eksiseyler.com/sitemap.xml"
OUTPUT_FILE = "eksiseyler_links.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def main():
    response = requests.get(SITEMAP_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    links = []
    for url in root.findall("sm:url", ns):
        loc = url.findtext("sm:loc", namespaces=ns)
        lastmod = url.findtext("sm:lastmod", namespaces=ns)
        if loc:
            links.append({"url": loc.strip(), "lastmod": lastmod})

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)

    print(f"{len(links)} link kaydedildi → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
