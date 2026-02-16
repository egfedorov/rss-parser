import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from dateutil import parser as dateparser
from urllib.parse import urljoin

def generate():
    url = 'https://takiedela.ru/stories/'
    # 1. Добавляем заголовки, чтобы сайт не блокировал скрипт
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Проверка на ошибки 404/500
    except Exception as e:
        print(f"❌ Ошибка загрузки главной страницы: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Такие дела — Истории')
    fg.link(href=url, rel='alternate')
    fg.description('Материалы из раздела «Истории» сайта takiedela.ru')
    fg.language('ru')

    # Используем более надежный поиск: li с классом b-col внутри списка
    articles = soup.select('.b-col-list li.b-col')
    print(f"Найдено статей: {len(articles)}")

    for item in articles:
        title_tag = item.select_one('.b-material__head')
        link_tag = item.select_one('a.b-material__txt')
        description_tag = item.select_one('.b-material__lead')

        if not (title_tag and link_tag):
            continue

        title = title_tag.get_text(strip=True)
        link = urljoin(url, link_tag['href'])
        # Описание может отсутствовать у некоторых типов постов
        description = description_tag.get_text(strip=True) if description_tag else ""

        pub_date = None

        try:
            # Не забываем про headers и здесь
            article_response = requests.get(link, headers=headers, timeout=5)
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            # 2. Упрощаем поиск даты: ищем любой тег <time> с атрибутом datetime
            time_tag = article_soup.find('time', attrs={'datetime': True})
            
            if time_tag:
                parsed = dateparser.parse(time_tag['datetime'])
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                pub_date = parsed.astimezone(timezone.utc)
            else:
                # 3. Фолбэк: если даты нет в теге <time>, можно попробовать поискать в скриптах или мета-тегах
                print(f"‼️ Не найден <time> для {link}")
                # Если дата критична — пропускаем, если нет — можно ставить текущую
                # pub_date = datetime.now(timezone.utc) 
        except Exception as e:
            print(f"⚠️ Ошибка при парсинге статьи {link}: {e}")

        if not pub_date:
            continue

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file('takiedela.xml')
    print("✅ RSS-лента успешно обновлена: takiedela.xml")

if __name__ == '__main__':
    generate()
