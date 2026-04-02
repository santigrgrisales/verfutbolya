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
    'marokko': 'Marruecos',
    'iordanija': 'Jordania',
    'italija': 'Italia',
    'anglija': 'Inglaterra',
    'bahrejn': 'Bahrain',
    'Насьональ': 'Nacional',
    # common transliteration variants -> readable names
    'kubok': 'Copa',
    'seriia': 'Serie',
    'turnir': 'Tournament',
    'medunarodnyj': 'International',
    'seria': 'Serie',
    'seriya': 'Serie',
    'serija': 'Serie',
    '2-ja liga': 'Ligue Two',
    'professionalnaja liga': 'Liga Profesional',
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


def _safe_transliterate(s: str) -> str:
    """Transliterate Cyrillic -> Latin with simple sanity checks.

    Uses `translit` then `unidecode` as fallback. Rejects candidates that
    contain suspicious isolated uppercase letters inside words (e.g. "MeFdun...")
    and falls back to the other candidate when detected.
    """
    if not s:
        return s
    try:
        # only attempt on Cyrillic-containing strings
        if not re.search(r'[\u0400-\u04FF]', s):
            return s

        cand_translit = None
        if translit:
            try:
                cand_translit = translit(s, 'ru', reversed=True)
            except Exception:
                cand_translit = None

        cand_unidecode = None
        try:
            cand_unidecode = unidecode(s)
        except Exception:
            cand_unidecode = None

        # heuristic: reject candidate if it contains a single ASCII uppercase
        # letter between lowercase letters (common artifact seen as 'F').
        def looks_bad(c: str) -> bool:
            if not c:
                return True
            if re.search(r'(?<=\w)[A-Z](?=\w)', c):
                return True
            return False

        # prefer translit if present and looks sane, else unidecode
        if cand_translit and not looks_bad(cand_translit):
            return cand_translit
        if cand_unidecode and not looks_bad(cand_unidecode):
            return cand_unidecode
        # last resort: return whichever is non-empty (prefer unidecode)
        return cand_unidecode or cand_translit or s
    except Exception:
        return s


def normalize_league_name(text: str) -> str:
    if not text:
        return text
    out = text
    # transliterate first to improve matching
    out = _safe_transliterate(out)
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
    'jun': 'United',
    "kembrid": "Cambridge",
    'brazilija': 'Brazil',
    'portugalija': 'Portugal',
    'saragosa': 'Zaragoza',
    'lion': 'Lyon',
    'volfsburg': 'Wolfsburg',
    'kastelon': 'Castellón',
    'shapekoense': 'Chapecoense',
    'bojaka chiko': 'Boyacá Chicó',
    'sentral': 'Central',
    'suindon': 'Swindon',
    'perejra': 'Pereira',
    'olimpik dchejra': 'Olympic Safi',
    'монтеррей': 'Monterrey',
    'monterrej': 'Monterrey',
    'атлетико': 'Atlético',
    'насьональ': 'Nacional',
    'Кэмбридж Юн': 'Cambridge United',
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
    out = _safe_transliterate(out)
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
