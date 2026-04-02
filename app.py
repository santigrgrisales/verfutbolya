from flask import Flask, render_template, request
from scrapers.roja import obtener_iframe
from scrapers.playerhd import obtener_iframe_playerhd
from services.scraper_manager import get_all

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)


@app.route('/')
def index():
    # Force refresh while debugging availability so changes appear immediately
    matches, availability = get_all(force=True)
    print('[app] availability:', availability)
    return render_template('index.html', matches=matches, availability=availability)

@app.route('/redirect', methods=['GET', 'POST'])
def redirect_page():
    # Accept both GET (backwards compatibility) and POST (to avoid exposing URL in querystring)
    if request.method == 'POST':
        url_original = request.form.get('url')
        match_title = request.form.get('match', 'Partido en Vivo')
        src = request.form.get('src', '')
    else:
        url_original = request.args.get('url')
        match_title = request.args.get('match', 'Partido en Vivo')
        src = request.args.get('src', '')

    # dispatch to appropriate resolver based on source id
    if src == 'playerhd':
        stream_url_real = obtener_iframe_playerhd(url_original)
    else:
        stream_url_real = obtener_iframe(url_original)

    # If resolved URL looks like a YouTube script or non-embeddable JS (e.g. contains ytembeds),
    # try to re-resolve by fetching the original page and looking for an iframe or webplayer page.
    try:
        if stream_url_real and ("/ytembeds/" in stream_url_real or (stream_url_real.endswith('.js') and 'youtube.com' in stream_url_real)):
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url_original, headers=headers, timeout=6)
            if r.status_code == 200 and r.text:
                soup = BeautifulSoup(r.text, 'html.parser')
                # Prefer iframe if present
                iframe = soup.find('iframe')
                if iframe and iframe.get('src'):
                    candidate = iframe.get('src')
                    stream_url_real = candidate if candidate.startswith('http') else urljoin(url_original, candidate)
                else:
                    # look for links to webplayer2.php or similar endpoints
                    found = None
                    for a in soup.select('a[href]'):
                        href = a.get('href')
                        if not href:
                            continue
                        if any(x in href for x in ('webplayer2.php', 'export/webmasters.php', 'gowm.php', 'webplayer.php')):
                            found = href
                            break
                    if found:
                        stream_url_real = found if found.startswith('http') else urljoin(url_original, found)
    except Exception:
        # non-fatal: keep original resolved URL
        pass

    # Render redirect page with resolved stream URL (not exposing original in URL when POST used)
    return render_template('redirect.html', stream_url=stream_url_real, match_title=match_title)


@app.route('/embed', methods=['GET', 'POST'])
def embed_page():
    # Prefer POST to avoid exposing stream URL in querystring, but accept GET for convenience
    if request.method == 'POST':
        stream_url = request.form.get('stream_url')
        match_title = request.form.get('match_title', 'Partido en Vivo')
    else:
        stream_url = request.args.get('stream_url')
        match_title = request.args.get('match_title', 'Partido en Vivo')

    # Basic sanity: if no stream URL provided, render a small message
    if not stream_url:
        return "No stream URL provided", 400

    return render_template('embed.html', stream_url=stream_url, match_title=match_title)

if __name__ == '__main__':
    # SOLUCIÓN: Forzamos a Flask a usar el puerto 8000 para evitar el conflicto con el PID 4
    app.run(debug=True, port=8000)