import os
import sys
import requests
# allow running this file directly: add project root to sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bs4 import BeautifulSoup
from models.match import Match


def obtener_iframe(url_canal):
    headers = {"User-Agent": "Mozilla/5.0"}
    # si es relativo o vacío, devolver tal cual
    if not url_canal or not url_canal.startswith('http'):
        return url_canal

    try:
        res = requests.get(url_canal, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            iframe = soup.find('iframe')
            if iframe and 'src' in iframe.attrs:
                return iframe['src']
    except Exception:
        pass

    return url_canal


def scrape_futbollibre():
    """Scrapea https://www.futbollibre.net.pe/ y devuelve lista de Match.

    Cada `Match` contiene `options` con `name` (canal) y `link` (href absoluto
    apuntando al embed en futbollibre). Esto deja intactos los enlaces como en
    la Opción 2; si quieres los `iframe` reales, podemos resolverlos llamando
    a `obtener_iframe()` sobre cada opción cuando integres el scraper.
    """
    url = "https://www.futbollibre.net.pe/"
    headers = {"User-Agent": "Mozilla/5.0"}
    matches = []

    try:
        # la web carga la agenda vía https://goolhd.com/agenda.json (ver js/index.js)
        agenda_url = 'https://goolhd.com/agenda.json'
        resp = requests.get(agenda_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return matches

        data = resp.json()
        # estructura: {"data": [ {"id":..., "attributes": {"diary_hour":..., "diary_description":..., "embeds": {"data": [ ... ] } } }, ... ] }
        from datetime import datetime
        now = datetime.now()

        for item in data.get('data', []):
            attrs = item.get('attributes', {})
            diary_hour = attrs.get('diary_hour', '')
            match_name = attrs.get('diary_description', '')
            date_diary = attrs.get('date_diary') or ''

            # intentar construir datetime para el evento (no es obligatorio)
            event_dt = None
            try:
                if date_diary and diary_hour:
                    # date_diary expected ISO YYYY-MM-DD, diary_hour HH:MM:SS
                    event_dt = datetime.fromisoformat(f"{date_diary}T{diary_hour}")
                elif diary_hour:
                    # usar hoy como fecha
                    hh, mm, ss = diary_hour.split(':')[:3]
                    event_dt = now.replace(hour=int(hh), minute=int(mm), second=int(ss), microsecond=0)
            except Exception:
                event_dt = None

            # formato de hora para mostrar: HH:MM
            display_time = ''
            if diary_hour:
                try:
                    hh, mm, ss = diary_hour.split(':')
                    display_time = f"{int(hh):02d}:{int(mm):02d}"
                    # calcular segundos desde medianoche para ordenar solo por hora
                    time_seconds = int(hh) * 3600 + int(mm) * 60 + int(ss)
                except Exception:
                    display_time = diary_hour
            else:
                time_seconds = float('inf')

            partido = Match(match_name, display_time)
            partido.source = 'Futbol Libre'

            # almacenar segundos desde medianoche para ordenar solo por hora
            partido.time_seconds = time_seconds

            embeds = attrs.get('embeds', {}).get('data', [])
            for emb in embeds:
                eattrs = emb.get('attributes', {})
                channel_name = eattrs.get('embed_name', '')
                iframe = eattrs.get('embed_iframe', '')
                href_full = ''
                if iframe:
                    if iframe.startswith('/'):
                        href_full = 'https://www.futbollibre.net.pe' + iframe
                    else:
                        href_full = iframe

                if href_full:
                    partido.add_option(channel_name, href_full)

            if partido.options:
                matches.append(partido)

        # ordenar por hora del día (seconds desde medianoche). Eventos sin hora al final
        matches.sort(key=lambda m: getattr(m, 'time_seconds', float('inf')))

    except Exception:
        pass

    return matches


if __name__ == '__main__':
    # script de prueba rápido (no automático en producción)
    print('Probando conexión a', 'https://www.futbollibre.net.pe/')
    try:
        r = requests.get('https://www.futbollibre.net.pe/', headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        print('Status:', r.status_code)
        body_snippet = r.text[:800].replace('\n',' ')
        print('Snippet:', body_snippet[:500])
        print('Encontró <ul id="menu"?', ('<ul id="menu"' in r.text))
        print('toggle-submenu count:', r.text.count('toggle-submenu'))
        print('submenu count:', r.text.count('submenu'))
        print("'embed/eventos' count:", r.text.count('embed/eventos'))
        print("'wraper' present:", ('wraper' in r.text))
        if 'wraper' in r.text:
            idx = r.text.find('wraper')
            start = max(0, idx-300)
            print('Around wraper:', r.text[start:start+1200].replace('\n',' ')[:1000])
        print("'fetch(' in page:", 'fetch(' in r.text)
        print("'.ajax(' in page:", '.ajax(' in r.text)
        print("'XMLHttpRequest' in page:", 'XMLHttpRequest' in r.text)
    except Exception as e:
        print('Error petición:', e)

    matches = scrape_futbollibre()
    print('Matches encontrados:', len(matches))
    for m in matches:
        print(m.match_time, '-', m.match_name)
        for o in m.options:
            print('  *', o['name'], o['link'])
    # listar scripts para analizar cómo se llena el <ul id="menu">
    try:
        soup = BeautifulSoup(r.text, 'html.parser')
        scripts = soup.find_all('script')
        print('Scripts encontrados:', len(scripts))
        for i, s in enumerate(scripts[:10], 1):
            src = s.get('src')
            print(f'  Script {i} src:', src)
            if not src:
                txt = (s.string or '')[:200].replace('\n',' ')
                print('   inline snippet:', txt)
            else:
                # intentar recuperar scripts locales (relativos)
                if src.startswith('js/') or src.startswith('/js/'):
                    script_url = 'https://www.futbollibre.net.pe/' + src.lstrip('/')
                    try:
                        jsr = requests.get(script_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
                        print(f'   -> fetched {script_url} status', jsr.status_code)
                        print('   -> snippet:', jsr.text[:400].replace('\n',' ')[:300])
                    except Exception as e:
                        print('   -> error fetching script:', e)
    except Exception:
        pass

    # intentar obtener agenda.json (apunta a goolhd.com)
    try:
        agenda_url = 'https://goolhd.com/agenda.json'
        aj = requests.get(agenda_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        print('Agenda.json status:', aj.status_code)
        if aj.status_code == 200:
            print('Agenda snippet:', aj.text[:1000].replace('\n',' ')[:900])
    except Exception as e:
        print('Error fetching agenda.json:', e)
