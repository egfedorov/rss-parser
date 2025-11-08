import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

def generate():
    url = "https://novayagazeta.eu/authors/66"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article.idjya.article-list-item")

    fg = FeedGenerator()
    fg.id(url)
    fg.title("Новая Газета Европа — публикации Кати Орловой")
    fg.link(href=url, rel="alternate")
    fg.description("Лента статей Кати Орловой с сайта novayagazeta.eu")
    fg.language("ru")

    for a in articles:
        link_tag = a.select_one("a.TNSR0.material-reference")
        if not link_tag:
            continue
        link = link_tag.get("href").strip()

        # --- Заголовок и подзаголовок ---
        title_tag = a.select_one("h2.e7vUH")
        subtitle_tag = a.select_one("span.hIDBK")

        if title_tag:
            subtitle_inside = title_tag.select_one("span.hIDBK")
            if subtitle_inside:
                subtitle_inside.extract()
            title = title_tag.get_text(strip=True)
        else:
            title = ""

        subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else ""
        full_title = f"{title}: {subtitle}" if subtitle else title
        # --------------------------------

        category_tag = a.select_one("span.xK9Tb")
        section_tag = a.select_one("span.Rai3O")
        category = category_tag.get_text(strip=True) if category_tag else ""
        section = section_tag.get_text(strip=True) if section_tag else ""
        author = "Катя Орлова"

        time_tag = a.select_one("article-time[date-time]")
        if time_tag and time_tag.get("date-time"):
            try:
                ts = int(time_tag["date-time"]) / 1000
                pub_date = datetime.fromtimestamp(ts, tz=timezone.utc)
            except ValueError:
                pub_date = datetime.now(timezone.utc)
        else:
            pub_date = datetime.now(timezone.utc)

        img_tag = a.select_one("img")
        img_url = img_tag["src"] if img_tag and img_tag.get("src") else None

        fe = fg.add_entry()
        fe.id(link)
        fe.title(full_title)
        fe.link(href=link)
        fe.description(subtitle or full_title)
        fe.author({'name': author})
        fe.pubDate(pub_date)
        if category:
            fe.category(term=category)
        if section:
            fe.category(term=section)
        if img_url:
            fe.enclosure(img_url, 0, "image/jpeg")

    fg.rss_file("orlova.xml")

if __name__ == "__main__":
    generate()
