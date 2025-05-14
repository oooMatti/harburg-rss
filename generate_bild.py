import asyncio
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE_URL = "https://www.bild.de"
NEWS_URL = f"{BASE_URL}/"

async def fetch_articles():
    articles = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
        await page.goto(NEWS_URL, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_selector("article.stage-teaser")

        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        article_boxes = soup.select("article.stage-teaser")
        print(f"🔎 {len(article_boxes)} Artikel auf der Startseite gefunden.")

        for box in article_boxes[:10]:
            link_tag = box.select_one("a.anchor")
            title_tag = box.select_one("h3.teaser__title")
            img_tag = box.select_one("img")

            if not link_tag or not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            relative_link = link_tag.get("href")
            link = relative_link if relative_link.startswith("http") else BASE_URL + relative_link
            image_url = img_tag["src"] if img_tag else None

            print(f"➡️ Verarbeite Artikel: {title}")

            try:
                article_page = await browser.new_page()
                await article_page.goto(link, timeout=60000, wait_until='domcontentloaded')
                article_html = await article_page.content()
                article_soup = BeautifulSoup(article_html, "html.parser")

                article_body = article_soup.select("div.article-body p")
                teaser_html = "".join(str(p) for p in article_body[:3]) if article_body else "<p>Kein Inhalt gefunden.</p>"
                image_html = f'<img src="{image_url}" alt="{title}" style="max-width:100%;"><br>' if image_url else ""
                description_html = image_html + teaser_html

                pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0100")
                articles.append({
                    "title": title,
                    "link": link,
                    "description": description_html,
                    "pubDate": pub_date
                })

                await article_page.close()

            except Exception as e:
                print(f"❌ Fehler beim Verarbeiten des Artikels {title}:", e)

        await browser.close()

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
  <title>BILD Inland – Automatischer RSS-Feed</title>
  <link>{NEWS_URL}</link>
  <description>Automatisch generierter Feed von bild.de</description>
  <language>de-de</language>{rss_items}
</channel>
</rss>"""
    return rss_feed

def save_rss(content):
    Path("docs").mkdir(exist_ok=True)
    Path("docs/rss_bild.xml").write_text(content, encoding="utf-8")
    print("📂 Feed gespeichert in docs/rss_bild.xml")

if __name__ == "__main__":
    try:
        articles = asyncio.run(fetch_articles())
        if not articles:
            print("❗ Keine Artikel gefunden.")
        rss_content = generate_rss(articles)
        save_rss(rss_content)
    except Exception as e:
        print("❌ Fehler im Script:", e)
