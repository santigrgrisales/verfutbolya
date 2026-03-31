import requests
from bs4 import BeautifulSoup
from models.match import Match

# Función para usar MÁS ADELANTE (solo cuando el usuario haga click)
def obtener_iframe(url_canal):
    # Usar headers más parecidos a un navegador real para evitar respuestas distintas
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        # Referer puede influir en el contenido que el servidor devuelve
        "Referer": "https://www.futbollibre.net.pe/",
        "Connection": "close",
    }

    if not url_canal or not url_canal.startswith('http'):
        return url_canal

    # Si la URL contiene un parámetro `r` (base64) intentamos decodificarlo
    try:
        from urllib.parse import urlparse, parse_qs, unquote
        import base64

        parsed = urlparse(url_canal)
        qs = parse_qs(parsed.query)
        if 'r' in qs and qs['r']:
            rval = qs['r'][0]
            # algunos valores usan URL-safe base64, añadir padding si falta
            try:
                padding = '=' * (-len(rval) % 4)
                decoded = base64.urlsafe_b64decode(rval + padding).decode('utf-8')
                decoded = unquote(decoded)
                if decoded.startswith('http'):
                    return decoded
            except Exception:
                pass
    except Exception:
        pass

    try:
        res = requests.get(url_canal, headers=headers, timeout=8, allow_redirects=True)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # intentar primero buscar por id conocido
            iframe = soup.find('iframe', id='embedIframe') or soup.find('iframe')
            if iframe and 'src' in iframe.attrs:
                src = iframe['src']
                # si el src es relativo, convertir a absoluto usando la base
                if src.startswith('/'):
                    from urllib.parse import urljoin
                    return urljoin(url_canal, src)
                return src
    except Exception as e:
        print(f"Error extrayendo iframe: {e}")

    return url_canal

def scrape_roja():
    url = "https://www.rojadirectatv3.pl/" 
    headers = {"User-Agent": "Mozilla/5.0"}
    matches = []

    try:
        # Esto ahora tomará solo 1 o 2 segundos
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            menu = soup.find('ul', class_='menu')
            if not menu: return matches

            for li in menu.find_all('li', recursive=False):
                a_tag = li.find('a')
                if not a_tag: continue
                
                time_span = a_tag.find('span', class_='t')
                match_time = time_span.text.strip() if time_span else "En vivo"
                
                match_name = a_tag.text.replace(match_time, '').strip().strip('"').strip()
                partido = Match(match_name, match_time)
                
                
                sub_ul = li.find('ul')
                if sub_ul:
                    for sub_li in sub_ul.find_all('li', class_='subitem1'):
                        canal_a = sub_li.find('a')
                        if canal_a:
                            # AQUÍ ESTÁ EL TRUCO: Guardamos el link original, NO el iframe todavía
                            partido.add_option(canal_a.text.strip(), canal_a['href'])
                
                if partido.options:
                    matches.append(partido)
                    
    except Exception as e:
        print(f"Error: {e}")
        
    return matches