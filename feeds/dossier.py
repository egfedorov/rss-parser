import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

def parse_dossier_date(date_str):
    # Пример: 23.06.2025
    try:
        dt = datetime.strptime(date_str.strip(), '%d.%m.%Y')
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        print(f"❌ Не удалось распознать дату: {date_str}")
        return datetime.now(timezone.utc)

def generate():
    url = 'https://dossier.center/investigations/'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Центр «Досье» — Расследования')
    fg.link(href=url, rel='alternate')
    fg.description('Новые расследования Центра «Досье»')
    fg.language('ru')

    for art in soup.select('.elementor-post'):
        # Ссылка
        a_tag = art.select_one('a.elementor-post__thumbnail__link')
        if not a_tag:
            continue
        link = a_tag['href']

        # Картинка
        img_tag = art.select_one('.elementor-post__thumbnail img')
        image_url = img_tag['src'] if img_tag else ''

        # Заголовок
        title_tag = art.select_one('h3.elementor-post__title a')
        title = title_tag.get_text(strip=True) if title_tag else 'Без названия'

        # Описание
        desc_tag = art.select_one('.elementor-post__excerpt p')
        description = desc_tag.get_text(strip=True) if desc_tag else ''

        # Дата публикации
        date_tag = art.select_one('.elementor-post-date')
        date_str = date_tag.get_text(strip=True) if date_tag else ''
        pub_date = parse_dossier_date(date_str)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        if description:
            fe.description(description)
        fe.pubDate(pub_date)
        if image_url:
            fe.enclosure(image_url, 0, 'image/jpeg')

    fg.rss_file('dossier.xml')

if __name__ == '__main__':
    generate()
