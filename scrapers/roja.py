import requests
from bs4 import BeautifulSoup
from models.match import Match

# Función para usar MÁS ADELANTE (solo cuando el usuario haga click)
def obtener_iframe(url_canal):
    headers = {"User-Agent": "Mozilla/5.0"}
    if not url_canal.startswith('http'):
        return url_canal 
        
    try:
        res = requests.get(url_canal, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            iframe = soup.find('iframe')
            if iframe and 'src' in iframe.attrs:
                return iframe['src'] 
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