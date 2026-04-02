import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.scraper_manager import get_all
print('Imported scraper_manager')
try:
    matches, availability = get_all()
    print('availability keys:', list(availability.keys()))
except Exception as e:
    print('error running get_all():', e)
