import time
import concurrent.futures
from typing import Dict, List, Tuple

from scrapers.futbollibre import scrape_futbollibre
from scrapers.roja import scrape_roja
from scrapers.playerhd import scrape_playerhd

# Per-scraper timeout (seconds)
# Aumentado para dar más margen a scrapers que tardan en responder
SCRAPE_TIMEOUT = 10
# Cache TTL for scraper results (seconds)
CACHE_TTL = 300

_cache: Dict[str, Dict] = {}

SCRAPERS = [
    ("Futbol Libre", scrape_futbollibre),
    ("Tarjeta Roja", scrape_roja),
    ("PlayerHD", scrape_playerhd),
]

def _fetch_source(name: str, fn):
    try:
        # pass the global timeout to scrapers that accept a timeout parameter
        try:
            matches = fn(timeout=SCRAPE_TIMEOUT) or []
        except TypeError:
            matches = fn() or []
        for m in matches:
            try:
                m.source = name
                # lightweight id for use in URLs (no spaces, lowercase)
                try:
                    m.source_id = name.replace(' ', '').lower()
                except Exception:
                    m.source_id = name.lower()
            except Exception:
                pass
        return matches, None
    except Exception as e:
        return [], str(e)

def update_all() -> Dict[str, Dict]:
    results: Dict[str, Dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SCRAPERS)) as ex:
        future_map = {ex.submit(_fetch_source, name, fn): name for name, fn in SCRAPERS}
        # Wait for all futures with a timeout; handle unfinished futures gracefully
        done, not_done = concurrent.futures.wait(list(future_map.keys()), timeout=SCRAPE_TIMEOUT + 1)

        # Collect results. Give a small buffer for futures that finish shortly after wait() returns.
        for fut in list(future_map.keys()):
            name = future_map.get(fut)
            try:
                # Wait up to 2s for any non-done future to finish gracefully
                matches, err = fut.result(timeout=2)
                results[name] = {"matches": matches, "error": err, "ts": time.time()}
            except concurrent.futures.TimeoutError:
                # still not finished: attempt cancel and mark as timeout
                try:
                    fut.cancel()
                except Exception:
                    pass
                results[name] = {"matches": [], "error": "timeout", "ts": time.time()}
            except Exception as e:
                results[name] = {"matches": [], "error": str(e), "ts": time.time()}

    # Ensure every scraper has an entry (timeouts etc.)
    for name, _ in SCRAPERS:
        if name not in results:
            results[name] = {"matches": [], "error": "timeout", "ts": time.time()}

    # update cache
    for name, data in results.items():
        # debug log: show how many matches each scraper returned
        try:
            cnt = len(data.get('matches', []))
        except Exception:
            cnt = 0
        print(f"[scraper_manager] result for {name}: matches={cnt} error={data.get('error')}")
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
            matches = entry.get("matches", [])
            availability[name] = len(matches) > 0
        return combined, availability

    # else perform update
    update_all()
    # no special-case synchronous retries required
    combined = []
    availability = {}
    for name, _ in SCRAPERS:
        entry = _cache.get(name, {})
        combined.extend(entry.get("matches", []))
        matches = entry.get("matches", [])
        availability[name] = len(matches) > 0
    return combined, availability

def force_refresh() -> Tuple[List, Dict[str, bool]]:
    return get_all(force=True)
