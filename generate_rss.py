import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

BASE_URL = "https://harburg-aktuell.de"
NEWS_URL = f"{BASE_URL}/"

def fetch_articles():
    response = requests.get(NEWS_URL)
    if response.status_code != 200:
        print(f"❌ Fehler beim Laden der Startseite ({response.status_code})")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    articles = []

    article_boxes = soup.select("div.article")
    print(f"🔎 {len(article_boxes)} Artikel auf der Startseite gefunden.")

    for item in article_boxes[:5]:  # Anzahl der Artikel im Feed
        title_tag = item.select_one("div.article-header h2 a")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        relative_link = title_tag.get("href", "")
        link = BASE_URL + relative_link

        print(f"➡️ Verarbeite Artikel: {title}")

        # Detailseite abrufen
        article_response = requests.get(link)
        if article_response.status_code != 200:
            print(f"❌ Fehler beim Laden der Detailseite: {link}")
            continue

        article_soup = BeautifulSoup(article_response.content, "html.parser")

        # Artikeltext
        body_tag = article_soup.select_one('[itemprop="articleBody"]')
        paragraphs = body_tag.select("p") if body_tag else []
        teaser_html = "".join(str(p) for p in paragraphs[:2]) if paragraphs else "<p>Kein Inhalt gefunden.</p>"

        # Bild
        image_tag = article_soup.select_one("div.article-full-image img")
        image_url = BASE_URL + image_tag["src"] if image_tag else None
        image_html = f'<img src="{image_url}" alt="{title}" style="max-width:100%;"><br>' if image_url else ""

        # Gesamtbeschreibung (Bild + Text)
        description_html = image_html + teaser_html

        pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0100")

        articles.append({
            "title": title,
            "link": link,
            "description": description_html,
            "pubDate": pub_date
        })

    print(f"✅ {len(articles)} Artikel erfolgreich verarbeitet.")
    return articles

def generate_rss(articles):
    rss_items = ""
    for item in articles:
        rss_items += f"""
  <item>
    <title>{item['title']}</title>
    <link>{item['link']}</link>
    <description><![CDATA[{item['description']}]]></description>
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
    Path("docs/rss.xml").write_text(content, encoding="utf-8")
    print("💾 Feed gespeichert in docs/rss.xml")

if __name__ == "__main__":
    try:
        articles = fetch_articles()
        if not articles:
            print("❗ Keine Artikel gefunden.")
        rss_content = generate_rss(articles)
        save_rss(rss_content)
    except Exception as e:
        print("❌ Fehler im Script:", e)
