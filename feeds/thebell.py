import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

def generate():
    url = "https://thebell.io/category/istorii"
    base_url = "https://thebell.io"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    fg = FeedGenerator()
    fg.title("The Bell — Истории")
    fg.link(href=url)
    fg.description("Новые статьи из раздела 'Истории' на The Bell")

    articles = soup.find_all("div", class_="grid-container")

    for article in articles:
        try:
            a_tag = article.find("a", class_="full-block-link")
            link = base_url + a_tag["href"]
            title = article.find("div", class_="text").get_text(strip=True)
            date_str = article.find("div", class_="time").get_text(strip=True)
            pub_date = parse_date(date_str)

            fe = fg.add_entry()
            fe.title(title)
            fe.link(href=link)
            fe.guid(link)
            fe.pubDate(pub_date)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            continue

    fg.rss_file("feed_thebell.xml")
    print("✅ thebell: сгенерирован feed_thebell.xml")

def parse_date(date_str):
    months = {
        "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
        "мая": "05", "июня": "06", "июля": "07", "августа": "08",
        "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12"
    }
    parts = date_str.strip().split()
    if len(parts) == 3:
        day = parts[0]
        month = months[parts[1]]
        year = parts[2]
        dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
    else:
        dt = datetime.now()
    return dt.replace(tzinfo=timezone.utc)
