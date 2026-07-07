"""
News module - Bundle.app API üzerinden Gündem ve Teknoloji haberlerini çeker.
"""
import json
import logging
import os
import time

import requests

BUNDLE_APP_BANNER = "https://www.bundle.app/api/main/get-banner"
BUNDLE_APP_POPULAR = "https://www.bundle.app/api/main/get-popular"
CACHE_FILE = "news_cache.json"
CACHE_TTL = 1800  # 30 dakika

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

CATEGORIES = [
    ("Gündem", "/gundem"),
    ("Teknoloji", "/bilim"),
]


def _safe_request(url: str):
    """HTTP GET isteği yapar, hata durumunda None döner."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logging.warning(f"⚠️ İstek başarısız ({url}): {e}")
        return None


def _fetch_from_endpoint(category_slug: str, endpoint: str) -> list[dict]:
    """
    Bundle.app API endpoint'inden haberleri çeker.

    Args:
        category_slug: Kategori slug'ı (örn: /gundem)
        endpoint: 'get-banner' veya 'get-popular'

    Returns:
        Haber listesi
    """
    base_url = BUNDLE_APP_BANNER if endpoint == "get-banner" else BUNDLE_APP_POPULAR
    api_url = f"{base_url}?locale=tr&page={category_slug}"

    response = _safe_request(api_url)
    if response is None:
        return []

    try:
        data = response.json()
    except ValueError as e:
        logging.error(f"❌ JSON parse hatası ({endpoint} - {category_slug}): {e}")
        return []

    news_items = []
    for item in data.get("newsSummaryList", [])[:20]:
        news_items.append({
            "source": endpoint,
            "channel_logo_src": item.get("channel_logo_src"),
            "channel_name": item.get("channel_name"),
            "title": item.get("title"),
            "link": item.get("link"),
            "pubdate": item.get("pubdate"),
        })

    return news_items


def _fetch_all() -> dict:
    """Gündem ve Teknoloji kategorilerinden haberleri çeker."""
    all_news = {}
    for cat_name, cat_slug in CATEGORIES:
        banner = _fetch_from_endpoint(cat_slug, "get-banner")
        popular = _fetch_from_endpoint(cat_slug, "get-popular")
        all_news[cat_name] = banner + popular
        logging.info(f"✅ {cat_name}: {len(all_news[cat_name])} haber alındı")
    return all_news


def get_news() -> dict:
    """
    Cache üzerinden haber verilerini getirir, TTL dolmuşsa yenisini çeker.

    Returns:
        {'Gündem': [...], 'Teknoloji': [...]} formatında haber sözlüğü
    """
    # Cache kontrolü
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cached = json.load(f)
            if time.time() - cached.get("last_updated", 0) < CACHE_TTL:
                logging.info("📦 Haberler cache'den yüklendi")
                return cached.get("news", {})
        except (json.JSONDecodeError, KeyError):
            pass

    # Yeni veri çek
    logging.info("🌐 Haberler API'den çekiliyor...")
    news = _fetch_all()

    # Cache'e kaydet
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_updated": time.time(), "news": news}, f, ensure_ascii=False)
    except OSError as e:
        logging.warning(f"⚠️ Cache kaydedilemedi: {e}")

    return news