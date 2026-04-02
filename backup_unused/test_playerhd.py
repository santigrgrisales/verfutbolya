from scrapers.playerhd import scrape_playerhd, obtener_iframe_playerhd

if __name__ == '__main__':
    ms = scrape_playerhd(limit=20, timeout=8)
    print(f"Matches encontrados: {len(ms)}")
    for m in ms:
        print('-', m.match_name, m.match_time, 'options:', len(m.options))

    if ms:
        # try resolving first match
        link = ms[0].options[0]['link']
        print('Resolving iframe for', link)
        print('iframe ->', obtener_iframe_playerhd(link))
