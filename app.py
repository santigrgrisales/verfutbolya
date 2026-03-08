from flask import Flask, render_template, request
from scrapers.roja import scrape_roja, obtener_iframe
import time

app = Flask(__name__)

cache_partidos = []
ultimo_scrape = 0
TIEMPO_CACHE = 900 # 15 minutos

@app.route('/')
def index():
    global cache_partidos, ultimo_scrape
    tiempo_actual = time.time()
    
    # Carga súper rápida: Solo entra a la página principal 1 vez cada 15 min
    if tiempo_actual - ultimo_scrape > TIEMPO_CACHE or not cache_partidos:
        print("Obteniendo lista de partidos...")
        cache_partidos = scrape_roja()
        ultimo_scrape = tiempo_actual

    return render_template('index.html', matches=cache_partidos)

@app.route('/redirect')
def redirect_page():
    # 1. Recibimos el link original (ej. tarjeta-roja.com/canal-1)
    url_original = request.args.get('url')
    match_title = request.args.get('match', 'Partido en Vivo')
    
    # 2. AQUÍ OBTENEMOS EL IFRAME: Entramos a ese link específico a sacar el video real
    stream_url_real = obtener_iframe(url_original)
    
    # 3. Mandamos el link real a nuestra plantilla de redirección
    return render_template('redirect.html', stream_url=stream_url_real, match_title=match_title)

if __name__ == '__main__':
    # SOLUCIÓN: Forzamos a Flask a usar el puerto 8000 para evitar el conflicto con el PID 4
    app.run(debug=True, port=8000)