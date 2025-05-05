
import asyncio
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://www.mopo.de/hamburg/"
RSS_FILE = "docs/rss_mopo.xml"

def fetch_articles():
    articles = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL, timeout=60000)
        content = page.content()
        soup = BeautifulSoup(content, "html.parser")

        article_boxes = soup.select("div.main-preview")
        print(f"🔎 {len(article_boxes)} Artikel auf der Startseite gefunden.")

        for item in article_boxes[:5]:
            title_tag = item.select_one("div.main-preview__post-title a")
            img_tag = item.select_one("img")
            if not title_tag or not img_tag:
                continue

            title = title_tag.get_text(strip=True)
            link = title_tag.get("href")
            image_url = img_tag.get("src")

            print(f"➡️ Verarbeite Artikel: {title}")

            # Detailseite öffnen
            article_page = browser.new_page()
            article_page.goto(link, timeout=60000)
            article_soup = BeautifulSoup(article_page.content(), "html.parser")
            article_page.close()

            body_container = article_soup.select_one("div.elementor-widget-container")
            paragraphs = body_container.select("p") if body_container else []
            teaser_html = "".join(str(p) for p in paragraphs[:4]) if paragraphs else "<p>Kein Inhalt gefunden.</p>"

            image_html = f'<img src="{image_url}" alt="{title}" style="max-width:100%;"><br>' if image_url else ""
            description_html = image_html + teaser_html

            pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0100")

            articles.append({
                "title": title,
                "link": link,
                "description": description_html,
                "pubDate": pub_date
            })

        browser.close()
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
  <title>MOPO Hamburg – Automatischer RSS-Feed</title>
  <link>{BASE_URL}</link>
  <description>Automatisch generierter Feed von mopo.de Hamburg</description>
  <language>de-de</language>{rss_items}
</channel>
</rss>"""
    return rss_feed

def save_rss(content):
    Path("docs").mkdir(exist_ok=True)
    Path(RSS_FILE).write_text(content, encoding="utf-8")
    print(f"💾 Feed gespeichert in {RSS_FILE}")

if __name__ == "__main__":
    try:
        articles = fetch_articles()
        if not articles:
            print("❗ Keine Artikel gefunden.")
        rss_content = generate_rss(articles)
        save_rss(rss_content)
    except Exception as e:
        print("❌ Fehler im Script:", e)
