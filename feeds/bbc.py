import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

def parse_bbc_date(date_str):
    # Пример: '2025-07-17'
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        print(f"❌ Не удалось распознать дату: {date_str}")
        return datetime.now(timezone.utc)

def generate():
    url = "https://www.bbc.com/russian/topics/cv27xky1pppt"
    resp = requests.get(url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    fg = FeedGenerator()
    fg.title("BBC Russian — Россия")
    fg.link(href=url, rel="alternate")
    fg.description("Главные новости России на русском от BBC")
    fg.language("ru")

    for li in soup.select("ul[data-testid='topic-promos'] > li"):
        # Ссылка и заголовок
        a_tag = li.select_one(".promo-text h3 a")
        if not a_tag:
            continue
        link = a_tag.get("href")
        if not link.startswith("http"):
            link = "https://www.bbc.com" + link
        title = a_tag.get_text(strip=True)

        # Описание
        desc_tag = li.select_one(".promo-text p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # Дата публикации (ISO, всегда есть у новостных)
        time_tag = li.select_one(".promo-text time[datetime]")
        if time_tag and time_tag.has_attr("datetime"):
            pub_date = parse_bbc_date(time_tag["datetime"])
        else:
            pub_date = datetime.now(timezone.utc)

        # Картинка (любая, лучше — максимальное качество из srcset)
        img_tag = li.select_one("img")
        image = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        if description:
            fe.description(description)
        fe.pubDate(pub_date)
        if image:
            fe.enclosure(image, 0, "image/jpeg")

    fg.rss_file("bbc.xml")

if __name__ == "__main__":
    generate()
