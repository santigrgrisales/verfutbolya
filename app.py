from flask import Flask, render_template, request
from scrapers.roja import obtener_iframe
from scrapers.playerhd import obtener_iframe_playerhd
from services.scraper_manager import get_all

import time

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

    # Render redirect page with resolved stream URL (not exposing original in URL when POST used)
    return render_template('redirect.html', stream_url=stream_url_real, match_title=match_title)

if __name__ == '__main__':
    # SOLUCIÓN: Forzamos a Flask a usar el puerto 8000 para evitar el conflicto con el PID 4
    app.run(debug=True, port=8000)