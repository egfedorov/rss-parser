import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime, timezone
import re

def parse_date_from_card(card):
    # Ищем .date-on-card-wrapper внутри карточки
    date_wrap = card.select_one('.date-on-card-wrapper')
    if not date_wrap:
        return None
    date_items = date_wrap.select('.date-on-card')
    # Убедимся, что получили три части: день, месяц, год
    if len(date_items) == 3:
        day = date_items[0].text.strip()
        month_raw = date_items[1].text.strip().lower()
        year = date_items[2].text.strip()
        # Русский и английский словари месяцев
        months = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
            'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        try:
            m = months[month_raw]
            d = int(day)
            y = int(year)
            return datetime(y, m, d, 12, 0, tzinfo=timezone.utc)
        except Exception as e:
            print(f"❌ Ошибка разбора даты {day} {month_raw} {year}: {e}")
    return None

def extract_image(style):
    m = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
    return m.group(1) if m else None

def generate():
    url = 'https://www.groza.media/'
    base_url = url

    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Гроза — главная')
    fg.link(href=base_url, rel='alternate')
    fg.description('Главные материалы сайта groza.media')
    fg.language('ru')

    for art in soup.select('.pic-item.w-dyn-item'):
        link_tag = art.select_one('a.pic-post-link')
        if not link_tag:
            continue
        href = link_tag.get('href')
        abs_url = urljoin(base_url, href)
        # Картинка
        image_div = art.select_one('.post-image-wrapper.emerge')
        image_url = extract_image(image_div['style']) if image_div else None
        # Заголовок и описание
        names = art.select('.post-name-text-in-grids.bigger')
        title = names[0].get_text(strip=True) if names else 'Без названия'
        desc_tag = art.select_one('.post-name-text-in-grids.description.bigger')
        desc = desc_tag.get_text(strip=True) if desc_tag else ''
        # Дата (теперь с главной!)
        pub_date = parse_date_from_card(art)
        if not pub_date:
            print(f"❌ Не удалось найти дату для {abs_url}, пропускаю материал.")
            continue

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=abs_url)
        if desc:
            fe.description(desc)
        fe.pubDate(pub_date)
        if image_url:
            fe.enclosure(image_url, 0, 'image/webp')

    fg.rss_file('groza.xml')

if __name__ == '__main__':
    generate()
