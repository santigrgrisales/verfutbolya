import re
from typing import Dict

# Optional transliteration libraries (best-effort)
try:
    from transliterate import translit
except Exception:
    translit = None

try:
    from unidecode import unidecode
except Exception:
    def unidecode(s: str) -> str:
        return s

# League/country normalization map: common transliteration variants and
# Cyrillic originals mapped to readable Spanish/English equivalents.
LEAGUE_NORMALIZATION: Dict[str, str] = {
    'Аргентина': 'Argentina',
    'Кубок': 'Copa',
    'gruppa': 'Grupo',
    'Бразилия': 'Brasil',
    'Серия': 'Serie',
    'Примера': 'Primera',
    'Мексика': 'México',
    'Женщины': 'Femenil',
    'Лига': 'Liga',
    'Колумбия': 'Colombia',
    'armenija': 'Armenia',
    'ispanija': 'España',
    'rumynija': 'Rumania',
    'iordanija': 'Jordania',
    'italija': 'Italia',
    'bahrejn': 'Bahrain',
    'Насьональ': 'Nacional',
    # common transliteration variants -> readable names
    'kubok': 'Copa',
    'seriia': 'Serie',
    'seria': 'Serie',
    'seriya': 'Serie',
    'serija': 'Serie',
    'primera': 'Primera',
    'zhenschiny': 'Femenil',
    'zhenshchiny': 'Femenil',
    'zh': 'F',
    'meksika': 'México',
    'braziliia': 'Brasil',
    'brazilija': 'Brasil',
    'kolumbiia': 'Colombia',
    'kolumbija': 'Colombia',
    'argentina': 'Argentina',
    'liga': 'Liga',
    'premer-liga': 'Premier League',
    # lowercase Cyrillic variants
    'аргентина': 'Argentina',
    'кубок': 'Copa',
    'бразилия': 'Brasil',
    'серия': 'Serie',
    'серия a': 'Serie A',
    'liga chempionov': 'Champions League',
    'примера': 'Primera',
    'мексика': 'México',
    'женщины': 'Femenil',
    'лига': 'Liga',
    'колумбия': 'Colombia',
    # some team/competition fixes often seen embedded in league text
    'korintians': 'Corinthians',
    'korinthians': 'Corinthians',
    'amerika': 'América',
    'america (zh)': 'América (F)',
    'atletiko nasional': 'Atlético Nacional',
    "atletiko nasional": 'Atlético Nacional',
    "nas'onal'": 'Nacional',
    'kukuta deportivo': 'Cúcuta Deportivo',
}


def _transliterate_if_cyrillic(s: str) -> str:
    if not s:
        return s
    try:
        if re.search(r'[\u0400-\u04FF]', s):
            if translit:
                try:
                    return translit(s, 'ru', reversed=True)
                except Exception:
                    return unidecode(s)
            return unidecode(s)
    except Exception:
        pass
    return s


def normalize_league_name(text: str) -> str:
    if not text:
        return text
    out = text
    # transliterate first to improve matching
    out = _transliterate_if_cyrillic(out)
    # remove stray apostrophes inside words produced by transliteration (e.g. Nas'onal')
    out = re.sub(r"(?<=\w)['’`]+(?=\w)", '', out)
    low = out.lower()
    for k, v in LEAGUE_NORMALIZATION.items():
        if k in low:
            out = re.sub(re.escape(k), v, out, flags=re.IGNORECASE)
            low = out.lower()
    out = re.sub(r'\s+\.', '.', out)
    out = re.sub(r"\s+", ' ', out).strip()
    return out


# Team / token normalization map
TEAM_NORMALIZATION: Dict[str, str] = {
    'atletiko': 'Atlético',
    'nasional': 'Nacional',
    'nasonal': 'Nacional',
    'almerija': 'Almeria',
    'barselona': 'Barcelona',
    'kastelon': 'Castellón',
    'монтеррей': 'Monterrey',
    'monterrej': 'Monterrey',
    'атлетико': 'Atlético',
    'насьональ': 'Nacional',
    'национал': 'Nacional',
    'atletiko nasional': 'Atlético Nacional',
    'kukuta': 'Cúcuta',
    'cucuta': 'Cúcuta',
    'amerika': 'América',
    'america': 'América',
    'korintians': 'Corinthians',
    'korinthians': 'Corinthians',
    # feminine marker variants
    '(zh)': '(F)',
    '(ж)': '(F)',
    'zh': 'F',
    'serija': 'Serie',
}


def normalize_team_name(text: str) -> str:
    if not text:
        return text
    out = text
    # transliterate first to improve matching
    out = _transliterate_if_cyrillic(out)
    # aggressively remove apostrophe-like characters produced by transliteration
    out = re.sub(r'["\'’`´]', '', out)
    low = out.lower()
    # apply token replacements
    for k, v in TEAM_NORMALIZATION.items():
        if k in low:
            out = re.sub(re.escape(k), v, out, flags=re.IGNORECASE)
            low = out.lower()
    out = re.sub(r"\s+", ' ', out).strip()
    return out
