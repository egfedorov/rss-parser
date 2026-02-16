import cloudscraper
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import timezone
from dateutil import parser as dateparser
from urllib.parse import urljoin
import time

def generate():
    url = 'https://takiedela.ru/stories/'
    
    # Создаем scraper вместо обычного requests
    # Он сам подставит нужные заголовки и решит базовые проверки Cloudflare
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Не удалось пробить защиту: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    fg = FeedGenerator()
    fg.title('Такие дела — Истории')
    fg.link(href=url, rel='alternate')
    fg.description('Материалы из раздела «Истории» сайта takiedela.ru')
    fg.language('ru')

    articles = soup.select('.b-col-list li.b-col')
    print(f"Найдено статей на странице: {len(articles)}")

    for item in articles:
        title_tag = item.select_one('.b-material__head')
        link_tag = item.select_one('a.b-material__txt')
        description_tag = item.select_one('.b-material__lead')

        if not (title_tag and link_tag):
            continue

        title = title_tag.get_text(strip=True)
        link = urljoin(url, link_tag['href'])
        description = description_tag.get_text(strip=True) if description_tag else ""

        pub_date = None

        try:
            # Делаем паузу 1-2 сек, чтобы не выглядеть как агрессивный парсер
            time.sleep(1) 
            
            article_response = scraper.get(link, timeout=10)
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            # Самый надежный поиск даты по тегу time
            time_tag = article_soup.find('time', attrs={'datetime': True})
            
            if time_tag:
                parsed = dateparser.parse(time_tag['datetime'])
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                pub_date = parsed.astimezone(timezone.utc)
                print(f"✅ Обработано: {title} ({pub_date})")
            else:
                print(f"‼️ Не нашли дату в {link}")

        except Exception as e:
            print(f"⚠️ Ошибка на статье {link}: {e}")

        if pub_date:
            fe = fg.add_entry()
            fe.title(title)
            fe.link(href=link)
            fe.description(description)
            fe.pubDate(pub_date)

    fg.rss_file('takiedela.xml')
    print("\nГотово! Файл takiedela.xml обновлен.")

if __name__ == '__main__':
    generate()
