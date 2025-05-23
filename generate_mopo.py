import asyncio
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE_URL = "https://www.mopo.de"
NEWS_URL = f"{BASE_URL}/hamburg/"

def parse_date_from_text(text):
    try:
        return datetime.strptime(text.strip(), "%d.%m.%Y / %H:%M")
    except Exception as e:
        print(f"❌ Fehler beim Parsen des Datums: {e}")
        return None

async def fetch_articles():
    articles = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
        await page.goto(NEWS_URL, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_selector("div.main-preview", timeout=10000)

        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        article_boxes = soup.select("div.main-preview")
        print(f"🔎 {len(article_boxes)} Artikel auf der Startseite gefunden.")

        for box in article_boxes[:15]:
            title_tag = box.select_one(".main-preview__title-link p")
            link_tag = box.select_one("a.main-preview__title-link")
            img_tag = box.select_one("img")

            if not title_tag or not link_tag:
                continue

            title = title_tag.get_text(strip=True)
            link = link_tag.get("href")
            image_url = img_tag["src"] if img_tag else None
            if not link.startswith("http"):
                link = BASE_URL + link

            print(f"➡️ Verarbeite Artikel: {title}")
            article_page = None

            try:
                article_page = await browser.new_page()
                await article_page.goto(link, timeout=60000, wait_until='domcontentloaded')
                article_html = await article_page.content()
                article_soup = BeautifulSoup(article_html, "html.parser")

                # Veröffentlichungsdatum prüfen
                date_tag = article_soup.select_one("span.elementor-post-info__item--type-date")
                if date_tag:
                    pub_datetime = parse_date_from_text(date_tag.get_text())
                    if not pub_datetime or pub_datetime.date() != datetime.today().date():
                        print(f"⏭️ Artikel ist nicht von heute: {title}")
                        continue
                else:
                    print(f"⏭️ Kein Datum gefunden für Artikel: {title}")
                    continue

                # Inhalt sammeln
                paragraphs = article_soup.select("p")
                teaser_html = "".join(str(p) for p in paragraphs[:4]) if paragraphs else "<p>Kein Inhalt gefunden.</p>"
                image_html = f'<img src="{image_url}" alt="{title}" style="max-width:100%;"><br>' if image_url else ""
                description_html = image_html + teaser_html

                articles.append({
                    "title": title,
                    "link": link,
                    "description": description_html,
                    "pubDate": pub_datetime.strftime("%a, %d %b %Y %H:%M:%S +0100")
                })

            except Exception as e:
                print(f"❌ Fehler beim Verarbeiten des Artikels {title}:", e)
            finally:
                if article_page:
                    await article_page.close()

        await browser.close()

    print(f"✅ {len(articles)} neue Artikel erfolgreich verarbeitet.")
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
  <link>{NEWS_URL}</link>
  <description>Automatisch generierter Feed von MOPO Hamburg</description>
  <language>de-de</language>{rss_items}
</channel>
</rss>"""
    return rss_feed

def save_rss(content):
    Path("docs").mkdir(exist_ok=True)
    Path("docs/rss_mopo.xml").write_text(content, encoding="utf-8")
    print("📂 Feed gespeichert in docs/rss_mopo.xml")

if __name__ == "__main__":
    try:
        articles = asyncio.run(fetch_articles())
        if not articles:
            print("❗ Keine Artikel gefunden.")
        rss_content = generate_rss(articles)
        save_rss(rss_content)
    except Exception as e:
        print("❌ Fehler im Script:", e)
