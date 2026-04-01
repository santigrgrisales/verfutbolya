from flask import Flask, render_template, request
from scrapers.roja import obtener_iframe
from services.scraper_manager import get_all

import time

app = Flask(__name__)


@app.route('/')
def index():
    # get_all performs cached, parallel scraping and returns (matches, availability)
    matches, availability = get_all()
    return render_template('index.html', matches=matches, availability=availability)

@app.route('/redirect')
def redirect_page():
    # 1. Recibimos el link original (ej. tarjeta-roja.com/canal-1)
    url_original = request.args.get('url')
    match_title = request.args.get('match', 'Partido en Vivo')

    # 2. Obtener el iframe (resolución lazy cuando el usuario hace click)
    stream_url_real = obtener_iframe(url_original)

    # 3. Mandamos el link real a nuestra plantilla de redirección
    return render_template('redirect.html', stream_url=stream_url_real, match_title=match_title)

if __name__ == '__main__':
    # SOLUCIÓN: Forzamos a Flask a usar el puerto 8000 para evitar el conflicto con el PID 4
    app.run(debug=True, port=8000)