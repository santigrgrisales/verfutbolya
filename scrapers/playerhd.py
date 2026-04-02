import re
import time
from typing import List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from models.match import Match
from utils.normalizer import normalize_league_name, normalize_team_name
from datetime import datetime, timedelta, timezone

try:
    from transliterate import translit
except Exception:
    translit = None

try:
    from unidecode import unidecode
except Exception:
    def unidecode(s: str) -> str:  # fallback: no-op if library missing
        return s


def _transliterate_if_cyrillic(s: str) -> str:
    if not s:
        return s
    # quick check for Cyrillic characters
    if re.search(r'[\u0400-\u04FF]', s):
        # prefer transliterate.translit if available
        try:
            if translit:
                return translit(s, 'ru', reversed=True)
        except Exception:
            pass
        # fallback to unidecode which is fast
        try:
            return unidecode(s)
        except Exception:
            return s
    # if no cyrillic, return original
    return s


_LEAGUE_NORMALIZATION = {
    # Cyrillic originals
    'Аргентина': 'Argentina',
    'Кубок': 'Copa',
    'Бразилия': 'Brasil',
    'Серия': 'Serie',
    'Примера': 'Primera',
    'Мексика': 'México',
    'Женщины': 'Femenil',
    'Лига': 'Liga',
    'Колумбия': 'Colombia',
    # common transliteration variants -> readable names
    'kubok': 'Copa',
    'seriia': 'Serie',
    'seria': 'Serie',
    'seriya': 'Serie',
    'primera': 'Primera',
    'zhenschiny': 'Femenil',
    'zhenshchiny': 'Femenil',
    'zh': 'F',
    'meksika': 'México',
    'braziliia': 'Brasil',
    'brazilija': 'Brasil',
    'kolumbiia': 'Colombia',
    'argentina': 'Argentina',
    'liga': 'Liga',
}


def _normalize_league_name(s: str) -> str:
    if not s:
        return s
    out = s
    low = s.lower()
    for k, v in _LEAGUE_NORMALIZATION.items():
        if k in low:
            # replace occurrences case-insensitively
            out = re.sub(re.escape(k), v, out, flags=re.IGNORECASE)
    # minor cleanup: replace multiple spaces and stray punctuation
    out = re.sub(r'\s+\.', '.', out)
    out = re.sub(r"\s+", ' ', out).strip()
    return out

BASE_URL = 'https://playerhd.top'
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
}


def _normalize_src(src: str, base: str) -> str:
    if not src:
        return ''
    src = src.strip()
    if src.startswith('//'):
        return 'https:' + src
    if src.startswith('/'):
        return urljoin(base, src)
    return src


def scrape_playerhd(limit=40, timeout=6) -> List[Match]:
    """Scrape playerhd.top/sports for match listings.
    Only include entries that have a clickable link (class "title" with href).
    Return Match objects with lazy option pointing to the match page (relative href).
    """
    matches: List[Match] = []
    debug = '[playerhd]'
    try:
        resp = requests.get(urljoin(BASE_URL, '/sports/'), headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code != 200:
            print(f"{debug} failed to fetch listing: {resp.status_code}")
            return matches
        listing_url = urljoin(BASE_URL, '/sports/')
        soup = BeautifulSoup(resp.text, 'html.parser')
        page_base = listing_url

        # If the page embeds a widget via an iframe (common), follow the iframe src
        # and try to scrape the widget HTML instead. This handles cases like:
        # <iframe id="main-iframe" src="https://livetv873.me/export/...."></iframe>
        try:
            iframe = soup.select_one('iframe#main-iframe') or soup.find('iframe')
            if iframe and iframe.get('src'):
                iframe_src = _normalize_src(iframe.get('src'), page_base)
                print(f"{debug} following iframe src: {iframe_src}")
                r2 = requests.get(iframe_src, headers=DEFAULT_HEADERS, timeout=timeout)
                if r2.status_code == 200 and r2.text:
                    soup = BeautifulSoup(r2.text, 'html.parser')
                    page_base = iframe_src
                    # sometimes the widget contains a nested iframe; follow one more level
                    nested = soup.find('iframe')
                    if nested and nested.get('src'):
                        nested_src = _normalize_src(nested.get('src'), page_base)
                        print(f"{debug} following nested iframe src: {nested_src}")
                        r3 = requests.get(nested_src, headers=DEFAULT_HEADERS, timeout=timeout)
                        if r3.status_code == 200 and r3.text:
                            soup = BeautifulSoup(r3.text, 'html.parser')
                            page_base = nested_src
        except Exception:
            pass

        # Prefer parsing by rows (table rows or match-row containers) to avoid
        # picking unrelated anchors. This is more precise and avoids many
        # false positives compared to scanning every `a` on the page.
        seen = set()
        rows = soup.select('table tr')
        if not rows:
            rows = soup.select('.match-row, .event, .sportRow, tr')

        for row in rows:
            try:
                a = row.select_one('a.title') or row.find('a', href=True)
                if not a:
                    continue

                match_name = a.get_text(strip=True)
                # transliterate when cirillic present (fast no-op otherwise)
                match_name = _transliterate_if_cyrillic(match_name)
                # normalize common team tokens (Atlético, Cúcuta, (Zh)->(F), Corinthians, etc.)
                match_name = normalize_team_name(match_name)

                # extract league/competition metadata from the same row (e.g. <span class="cmp">)
                league = ''
                for sel in ('.cmp', 'span.cmp', '.competition', '.league', 'td .cmp', '.spr'):
                    try:
                        el = row.select_one(sel)
                    except Exception:
                        el = None
                    if el and el.get_text(strip=True):
                        league = el.get_text(strip=True)
                        league = _transliterate_if_cyrillic(league)
                        league = normalize_league_name(league)
                        break
                if league:
                    display_name = f"{league}: {match_name}"
                else:
                    display_name = match_name
                if not match_name or len(match_name) < 3:
                    continue

                href = a.get('href')
                if not href:
                    continue
                if href.startswith('#') or href.lower().startswith('javascript:'):
                    continue

                # Resolve relative links against the page base (could be the widget host)
                link = urljoin(page_base, href)
                if link in seen:
                    continue

                # skip obvious external hosts (we want site match pages)
                # allow links that belong to playerhd.top or to the current page_base host
                allowed_hosts = {urlparse(BASE_URL).netloc}
                try:
                    allowed_hosts.add(urlparse(page_base).netloc)
                except Exception:
                    pass
                if link.startswith('http'):
                    link_host = urlparse(link).netloc
                    if link_host not in allowed_hosts:
                        continue

                # extract time from known places inside the row
                match_time = ''
                time_el = None
                for sel in ('.time', 'td.time', 'span.time', '.hour'):
                    time_el = row.select_one(sel)
                    if time_el and time_el.get_text(strip=True):
                        match_time = time_el.get_text(strip=True)
                        break
                if not match_time:
                    m = re.search(r'\b(\d{1,2}:\d{2})\b', row.get_text(' ', strip=True))
                    if m:
                        match_time = m.group(1)

                # Convert assumed source time to local timezone.
                # PlayerHD doesn't provide timezone info; we assume a default
                # source offset (hours). This is a lightweight conversion
                # that avoids external dependencies. Adjust `PLAYERHD_TZ_OFFSET_HOURS`
                # if you know the correct source timezone.
                PLAYERHD_TZ_OFFSET_HOURS = 3  # default: UTC+3 (e.g., Moscow)
                try:
                    tm = re.match(r"^(\d{1,2}):(\d{2})$", match_time or "")
                    if tm:
                        hh = int(tm.group(1))
                        mm = int(tm.group(2))
                        src_tz = timezone(timedelta(hours=PLAYERHD_TZ_OFFSET_HOURS))
                        local_tz = datetime.now().astimezone().tzinfo
                        dt_src = datetime.combine(datetime.now().date(), datetime.min.time()).replace(hour=hh, minute=mm, second=0, microsecond=0, tzinfo=src_tz)
                        dt_local = dt_src.astimezone(local_tz)
                        match_time = dt_local.strftime('%H:%M')
                except Exception:
                    # if anything fails, keep original match_time
                    pass

                partido = Match(display_name, match_time or '')
                partido.add_option('Abrir partido', link)
                partido.source = 'PlayerHD'
                matches.append(partido)
                seen.add(link)

                if len(matches) >= limit:
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"{debug} error: {e}")

    return matches


def obtener_iframe_playerhd(match_page_url: str) -> str:
    """Resolve the real iframe URL from a PlayerHD match page.
    Returns absolute iframe src or original URL if not found.
    """
    headers = DEFAULT_HEADERS.copy()
    if not match_page_url or not match_page_url.startswith('http'):
        return match_page_url
    try:
        current = match_page_url
        max_depth = 4
        for depth in range(max_depth):
            r = requests.get(current, headers=headers, timeout=8)
            if r.status_code != 200:
                break
            text = r.text or ''
            soup = BeautifulSoup(text, 'html.parser')

            # 1) prefer iframe inside #playerblock
            player_block = soup.select_one('#playerblock')
            if player_block:
                iframe = player_block.find('iframe')
                if iframe and iframe.get('src'):
                    src = _normalize_src(iframe.get('src'), current)
                    if src == current:
                        return src
                    current = src
                    continue

            # 2) any iframe on page
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                src = _normalize_src(iframe.get('src'), current)
                # if this looks like a final embed (player/live.php or emb.), return it
                if re.search(r'player/(live|embed)\.php|/player/live\.php|/embed/', src):
                    return src
                if src == current:
                    return src
                current = src
                continue

            # 3) look for anchors that point to known webplayer endpoints (webplayer2.php, export/webmasters.php, gowm.php)
            a = None
            for candidate in soup.select('a[href]'):
                href = candidate.get('href')
                if not href:
                    continue
                if any(x in href for x in ('webplayer2.php', 'export/webmasters.php', 'gowm.php', 'webplayer.php')):
                    a = candidate
                    break
            if a:
                href = a.get('href')
                src = _normalize_src(href, current)
                if src == current:
                    return src
                current = src
                continue

            # 4) regex: search for direct embed urls in scripts
            m = re.search(r'(https?:)?//[^"\']*(player|emb)\.[^"\']+player[^"\']*|https?://[^"\']+player/live\.php\?id=\d+', text)
            if m:
                found = m.group(0)
                if found.startswith('//'):
                    found = 'https:' + found
                return found

            # 4b) look for gowm.php or webplayer2.php references and prefer livetv hosts
            # the widget sometimes includes links like '/gowm.php?lid=...&eid=...' which
            # should be resolved against an external livetv host (livetv873.me or cdn.livetv873.me)
            gw = re.search(r"(?:href=|href\:\s*|\s)(['\"]?)(/)?(gowm\.php\?[^'\"\s>]+)\1", text)
            if gw:
                gw_path = gw.group(3)
                # prefer cdn host if present in text, else use livetv873.me
                host = 'https://livetv873.me'
                if 'cdn.livetv873.me' in text:
                    host = 'https://cdn.livetv873.me'
                candidate = urljoin(host + '/', gw_path)
                if candidate and candidate != current:
                    current = candidate
                    continue

            wp = re.search(r'(https?:)?//[^"\']*?/webplayer2\.php\?[^"\']+', text)
            if wp:
                wp_url = wp.group(0)
                if wp_url.startswith('//'):
                    wp_url = 'https:' + wp_url
                return wp_url

            # 5) search any src-like assignment in JS
            m2 = re.search(r"src\s*[:=]\s*['\"](//[^'\"]+|/[^'\"]+|https?://[^'\"]+)['\"]", text)
            if m2:
                src = _normalize_src(m2.group(1), current)
                if src and re.search(r'player/(live|embed)\.php|/player/live\.php|/embed/', src):
                    return src
                if src and src != current:
                    current = src
                    continue

            # nothing new found; break
            break

        # fallback: return the last attempted URL
        return current
    except Exception:
        return match_page_url
