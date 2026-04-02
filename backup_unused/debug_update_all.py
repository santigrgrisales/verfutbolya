from services.scraper_manager import update_all

if __name__ == '__main__':
    results = update_all()
    for name, data in results.items():
        print('---', name)
        print(' error:', data.get('error'))
        matches = data.get('matches') or []
        print(' matches_count:', len(matches))
        for m in matches[:5]:
            print('  -', getattr(m, 'match_name', None), 'opts:', len(getattr(m, 'options', [])))
