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

@app.route('/redirect')
def redirect_page():
    # 1. Recibimos el link original (ej. tarjeta-roja.com/canal-1)
    url_original = request.args.get('url')
    match_title = request.args.get('match', 'Partido en Vivo')

    # 2. Obtener el iframe (resolución lazy cuando el usuario hace click)
    src = request.args.get('src', '')
    # dispatch to appropriate resolver based on source id
    if src == 'playerhd':
        stream_url_real = obtener_iframe_playerhd(url_original)
    else:
        stream_url_real = obtener_iframe(url_original)

    # 3. Mandamos el link real a nuestra plantilla de redirección
    return render_template('redirect.html', stream_url=stream_url_real, match_title=match_title)

if __name__ == '__main__':
    # SOLUCIÓN: Forzamos a Flask a usar el puerto 8000 para evitar el conflicto con el PID 4
    app.run(debug=True, port=8000)