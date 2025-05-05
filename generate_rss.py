import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

BASE_URL = "https://harburg-aktuell.de"
NEWS_URL = f"{BASE_URL}/news.html"

def fetch_articles():
    response = requests.get(NEWS_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    articles = []

    for item in soup.select("div.item")[:10]:  # Beschränkt auf die neuesten 10 Artikel
        title_tag = item.select_one("h2 a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = BASE_URL + title_tag.get("href", "")
        description_tag = item.select_one("p")
        description = description_tag.get_text(strip=True) if description_tag else ""
        pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0100")  # Aktuelles Datum
        articles.append({
            "title": title,
            "link": link,
            "description": description,
            "pubDate": pub_date
        })
    return articles

def generate_rss(articles):
    rss_items = ""
    for item in articles:
        rss_items += f"""
  <item>
    <title>{item['title']}</title>
    <link>{item['link']}</link>
    <description>{item['description']}</description>
    <pubDate>{item['pubDate']}</pubDate>
  </item>"""

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Harburg Aktuell – Automatischer RSS-Feed</title>
  <link>{NEWS_URL}</link>
  <description>Automatisch generierter Feed von Harburg-Aktuell.de</description>
  <language>de-de</language>{rss_items}
</channel>
</rss>"""
    return rss_feed

def save_rss(content):
    Path("docs").mkdir(exist_ok=True)
    with open("docs/rss.xml", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    articles = fetch_articles()
    rss_content = generate_rss(articles)
    save_rss(rss_content)
