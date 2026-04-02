import re

# League/country normalization map: common transliteration variants and
# Cyrillic originals mapped to readable Spanish/English equivalents.
LEAGUE_NORMALIZATION = {
	'Аргентина': 'Argentina',
	'Кубок': 'Copa',
	'Бразилия': 'Brasil',
	'Серия': 'Serie',
	'Примера': 'Primera',
	'Мексика': 'México',
	'Женщины': 'Femenil',
	'Лига': 'Liga',
	'Колумбия': 'Colombia',
	'Насьональ': 'Nacional',
	# common transliteration variants -> readable names
	'kubok': 'Copa',
	'seriia': 'Serie',
	'seria': 'Serie',
	'seriya': 'Serie',
	'Serija': 'Serie',
	'primera': 'Primera',
	'zhenschiny': 'Femenil',
	'zhenshchiny': 'Femenil',
	'zh': 'F',
	'meksika': 'México',
	'braziliia': 'Brasil',
	'brazilija': 'Brasil',
	'kolumbiia': 'Colombia',
	'Kolumbija': 'Colombia',
	'argentina': 'Argentina',
	'liga': 'Liga',
	# lowercase keys (Cyrillic or transliteration) -> readable names
	'аргентина': 'Argentina',
	'кубок': 'Copa',
	'бразилия': 'Brasil',
	'серия': 'Serie',
	'серия a': 'Serie A',
	'примера': 'Primera',
	'мексика': 'México',
	'женщины': 'Femenil',
	'лига': 'Liga',
	'колумбия': 'Colombia',
	# common transliteration variants -> readable names
	'kubok': 'Copa',
	'seriia': 'Serie',
	'serija': 'Serie',
	'seria': 'Serie',
	'seriya': 'Serie',
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
	# some team name fixes
	'korintians': 'Corinthians',
	'korinthians': 'Corinthians',
	'amerika': 'América',
	'america (zh)': 'América (F)',
	'atletiko nasional': 'Atlético Nacional',
	"atletiko nasional": 'Atlético Nacional',
    "Nas'onal'": 'Nacional',
	'kukuta deportivo': 'Cúcuta Deportivo',
}


def normalize_league_name(text: str) -> str:
	if not text:
		return text
	out = text
	# remove stray apostrophes inside words produced by transliteration (e.g. Nas'onal')
	out = re.sub(r"(?<=\w)['’`]+(?=\w)", '', out)
	low = out.lower()
	for k, v in LEAGUE_NORMALIZATION.items():
		if k in low:
			out = re.sub(re.escape(k), v, out, flags=re.IGNORECASE)
	out = re.sub(r'\s+\.', '.', out)
	out = re.sub(r"\s+", ' ', out).strip()
	return out


# Team / token normalization map
TEAM_NORMALIZATION = {
	"atletiko": 'Atlético',
	"atletiko": 'Atlético',
	"nasional": 'Nacional',
	"nasonal": 'Nacional',
	'monterrej': 'Monterrey',
	'атлетико': 'Atlético',
	"насьональ": 'Nacional',
	"национал": 'Nacional',
	"atletiko nasional": 'Atlético Nacional',
	"kukuta": 'Cúcuta',
	"cucuta": 'Cúcuta',
	"amerika": 'América',
	"america": 'América',
	"korintians": 'Corinthians',
	"korinthians": 'Corinthians',
	# feminine marker variants
	'(zh)': '(F)',
	'(ж)': '(F)',
	'zh': 'F',
	"serija": 'Serie',
}


def normalize_team_name(text: str) -> str:
	if not text:
		return text
	out = text
	# aggressively remove apostrophe-like characters produced by transliteration
	out = re.sub(r"[\"'’`´]", '', out)
	low = out.lower()
	# apply token replacements
	for k, v in TEAM_NORMALIZATION.items():
		if k in low:
			out = re.sub(re.escape(k), v, out, flags=re.IGNORECASE)
			low = out.lower()
	out = re.sub(r"\s+", ' ', out).strip()
	return out

