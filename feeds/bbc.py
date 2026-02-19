import cloudscraper # Используем его, так как BBC любит проверять браузер
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from dateutil import parser as dateparser
from urllib.parse import urljoin

def generate():
    url = "https://www.bbc.com/russian/topics/cv27xky1pppt"
    
    # BBC может капризничать, поэтому берем scraper
    scraper = cloudscraper.create_scraper()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    try:
        resp = scraper.get(url, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Ошибка доступа к BBC: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    fg = FeedGenerator()
    fg.title("BBC Russian — Россия")
    fg.link(href=url, rel="alternate")
    fg.description("Главные новости России на русском от BBC")
    fg.language("ru")

    # 1. Собираем и Billboard (главную), и обычные промо-карточки
    # Ищем все li в списках и саму секцию Billboard
    items = soup.select('section[data-testid^="billboard"], [data-testid="topic-promos"] li')
    
    print(f"Найдено элементов для анализа: {len(items)}")

    for li in items:
        # 2. Ищем ссылку и заголовок (BBC стабильно держит их в h2 или h3)
        a_tag = li.find('a', class_=lambda x: x and 'css-' in x) # Ищем любую ссылку с динамическим классом
        if not a_tag:
            continue
            
        link = urljoin("https://www.bbc.com", a_tag.get("href"))
        # Заголовок часто внутри ссылки или в соседнем теге h2/h3
        title = a_tag.get_text(strip=True)

        # 3. Описание (ищем по стабильному классу 'promo-paragraph')
        desc_tag = li.select_one("p[class*='promo-paragraph']")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # 4. Дата (используем универсальный парсер)
        pub_date = datetime.now(timezone.utc)
        time_tag = li.find("time", attrs={"datetime": True})
        if time_tag:
            try:
                pub_date = dateparser.parse(time_tag["datetime"])
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
            except:
                pass

        # 5. Картинка (берем первую попавшуюся в блоке)
        img_tag = li.find("img")
        image = img_tag.get("src") if img_tag else ""
        
        # Если есть srcset, можно вытянуть картинку получше
        if img_tag and img_tag.has_attr('srcset'):
            # Берем самую большую из srcset (обычно последняя в списке)
            image = img_tag['srcset'].split(',')[-1].split(' ')[0]

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.id(link) # GUID для ридеров
        if description:
            fe.description(description)
        fe.pubDate(pub_date)
        if image:
            fe.enclosure(image, 0, "image/jpeg")

    fg.rss_file("bbc.xml", pretty=True)
    print("✅ RSS BBC обновлен!")

if __name__ == "__main__":
    generate()
