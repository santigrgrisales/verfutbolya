from services.scraper_manager import get_all

def main():
    matches, availability = get_all()
    print('matches:', len(matches))
    print('availability:', availability)

if __name__ == '__main__':
    main()
