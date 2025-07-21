import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re
import time

def parse_article_date(article_url):
    """
    Парсит дату публикации внутри статьи 7x7.
    Пример: <div class="article-header__date">18 июля, 9:43</div> или <div class="article-header__date">10 июля</div>
    """
    try:
        r = requests.get(article_url, timeout=5)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        # Универсальный поиск: ищем дату в первом подходящем div
        # Обычно: <div class="article-header__date">...</div>
        date_tag = soup.find(class_=re.compile(r'article-header__date'))
        if not date_tag:
            # fallback: ищем по пути, если верстка изменилась
            main = soup.find('main')
            if main:
                date_tag = main.find('div', string=re.compile(r'\d+ [а-я]+'))
        if not date_tag:
            print(f'❌ Не удалось найти дату на {article_url}')
            return None
        date_str = date_tag.get_text(strip=True)
        # Пример: "18 июля, 9:43" или "10 июля"
        months = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
            'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }
        now = datetime.now(timezone.utc)
        # "18 июля, 9:43"
        m = re.match(r'(\d{1,2}) ([а-яё]+), (\d{1,2}):(\d{2})', date_str)
        if m:
            day, month_str, hour, minute = m.groups()
            month = months[month_str.lower()]
            year = now.year
            dt = datetime(year, month, int(day), int(hour), int(minute), tzinfo=timezone.utc)
            # Если дата получилась в будущем — уменьшаем год на 1 (редкий случай)
            if dt > now:
                dt = dt.replace(year=year-1)
            return dt
        # "10 июля"
        m = re.match(r'(\d{1,2}) ([а-яё]+)', date_str)
        if m:
            day, month_str = m.groups()
            month = months[month_str.lower()]
            year = now.year
            dt = datetime(year, month, int(day), 12, 0, tzinfo=timezone.utc)
            if dt > now:
                dt = dt.replace(year=year-1)
            return dt
    except Exception as e:
        print(f"❌ Ошибка при парсинге даты {article_url}: {e}")
        return None
    print(f"❌ Не удалось распознать дату '{date_str}' на {article_url}")
    return None

def generate():
    url = 'https://semnasem.org/tags/istorii'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('7x7 — Истории')
    fg.link(href=url, rel='alternate')
    fg.description('Свежие материалы из раздела "Истории" на 7x7')
    fg.language('ru')

    for wrap in soup.select('.tag-materials-grid .material-teaser-wrap'):
        # Ссылка и картинка
        a_tag = wrap.select_one('a')
        if not a_tag:
            continue
        href = a_tag.get('href', '')
        if not href.startswith('http'):
            href = 'https://semnasem.org' + href
        img_div = a_tag.select_one('.material-teaser-illustration')
        image = ''
        if img_div and img_div.has_attr('style'):
            m = re.search(r"url\(['\"]?(.*?)['\"]?\)", img_div['style'])
            if m:
                image = m.group(1)
                if image.startswith('/'):
                    image = 'https://semnasem.org' + image

        # Дата публикации — внутри самой статьи
        pub_date = parse_article_date(href)
        if not pub_date:
            print(f"‼️ Пропуск материала без даты: {href}")
            continue
        # Заголовок и описание
        title_tag = wrap.select_one('.material-teaser-title')
        title = title_tag.get_text(strip=True) if title_tag else 'Без названия'
        desc_tag = wrap.select_one('.material-teaser-body-content')
        description = desc_tag.get_text(strip=True) if desc_tag else ''

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=href)
        if description:
            fe.description(description)
        fe.pubDate(pub_date)
        if image:
            fe.enclosure(image, 0, 'image/jpeg')

        # Немного усыпим скрипт, чтобы не нагружать сервер
        time.sleep(0.3)

    fg.rss_file('semnasem.xml')

if __name__ == '__main__':
    generate()
