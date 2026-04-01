import time
import concurrent.futures
from typing import Dict, List, Tuple

from scrapers.futbollibre import scrape_futbollibre
from scrapers.roja import scrape_roja

# Per-scraper timeout (seconds)
SCRAPE_TIMEOUT = 6
# Cache TTL for scraper results (seconds)
CACHE_TTL = 300

_cache: Dict[str, Dict] = {}

SCRAPERS = [
    ("Futbol Libre", scrape_futbollibre),
    ("Tarjeta Roja", scrape_roja),
]

def _fetch_source(name: str, fn):
    try:
        matches = fn() or []
        for m in matches:
            try:
                m.source = name
            except Exception:
                pass
        return matches, None
    except Exception as e:
        return [], str(e)

def update_all() -> Dict[str, Dict]:
    results: Dict[str, Dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SCRAPERS)) as ex:
        future_map = {ex.submit(_fetch_source, name, fn): name for name, fn in SCRAPERS}
        # Attempt to collect results with a global timeout
        for fut in concurrent.futures.as_completed(future_map, timeout=SCRAPE_TIMEOUT + 1):
            name = future_map[fut]
            try:
                matches, err = fut.result(timeout=1)
            except Exception as e:
                matches, err = [], str(e)
            results[name] = {"matches": matches, "error": err, "ts": time.time()}

    # Ensure every scraper has an entry (timeouts etc.)
    for name, _ in SCRAPERS:
        if name not in results:
            results[name] = {"matches": [], "error": "timeout", "ts": time.time()}

    # update cache
    for name, data in results.items():
        _cache[name] = data

    return results

def get_all(force: bool = False) -> Tuple[List, Dict[str, bool]]:
    now = time.time()
    valid = True
    for name, _ in SCRAPERS:
        entry = _cache.get(name)
        if not entry or now - entry.get("ts", 0) > CACHE_TTL:
            valid = False
            break

    if valid and not force:
        combined = []
        availability = {}
        for name, _ in SCRAPERS:
            entry = _cache.get(name, {})
            combined.extend(entry.get("matches", []))
            availability[name] = len(entry.get("matches", [])) > 0
        return combined, availability

    # else perform update
    update_all()
    combined = []
    availability = {}
    for name, _ in SCRAPERS:
        entry = _cache.get(name, {})
        combined.extend(entry.get("matches", []))
        availability[name] = len(entry.get("matches", [])) > 0
    return combined, availability

def force_refresh() -> Tuple[List, Dict[str, bool]]:
    return get_all(force=True)
