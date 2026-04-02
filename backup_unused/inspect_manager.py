from services.scraper_manager import get_all

if __name__ == '__main__':
    combined, availability = get_all(force=True)
    print('AVAILABILITY:', availability)
    print('TOTAL_MATCHES:', len(combined))
    print('SOURCES:', {m.source for m in combined})
    print('\nSAMPLE:')
    for m in combined:
        print(m.match_name, '|', getattr(m,'source',None), '| options:', len(m.options))
