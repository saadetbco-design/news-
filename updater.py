import os
import json
import feedparser
import urllib.request
import google.generativeai as genai
from datetime import datetime

GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Çoklu Haber Kaynakları Havuzu
RSS_SOURCES = [
    {"name": "Defense News", "cat": "military", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/"},
    {"name": "Naval News", "cat": "military", "url": "https://www.navalnews.com/feed/"},
    {"name": "Anadolu Ajansı Gündem", "cat": "turkey", "url": "https://www.aa.com.tr/tr/rss/default?cat=gundem"},
    {"name": "Al-Monitor", "cat": "regional", "url": "https://www.al-monitor.com/rss"}
]

def fetch_kapalicarsi_and_bist():
    # Kapalıçarşı ve BIST canlı gösterge şablonu
    return {
        "bist100": "10,840 (BIST)",
        "usd_try_kapalicarsi": "32.90 TL",
        "eur_try_kapalicarsi": "35.65 TL",
        "gram_altin_kapalicarsi": "2,540 TL",
        "aselsan": "₺62.40 (ASELS)"
    }

def fetch_all_sources():
    collected = []
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:2]:
                collected.append({
                    "source": source["name"],
                    "title": entry.title,
                    "summary": entry.get("summary", "")
                })
        except Exception as e:
            print(f"Hata ({source['name']}): {e}")
    return collected

def generate_brief(articles, markets):
    prompt = f"""
    Sen 'The Global Brief' platformunun baş istihbarat analizcisisin.
    Piyasalar: {json.dumps(markets, ensure_ascii=False)}
    Haberler: {json.dumps(articles, ensure_ascii=False)}

    SADECE geçerli bir JSON verisi döndür:
    {{
      "greeting": "Günaydın Saadet. Sistem hazır." veya "İyi Akşamlar Saadet. Sistem hazır.",
      "red_alert": "Son gelişmelere göre en kritik 1 cümlelik sıcak kriz haberi",
      "bullet_1": "Önemli gelişme 1 (Türkçe)",
      "bullet_2": "Önemli gelişme 2 (English)",
      "bullet_3": "Önemli gelişme 3 (Türkçe veya English)"
    }}
    """
    response = model.generate_content(prompt)
    clean = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

def main():
    markets = fetch_kapalicarsi_and_bist()
    articles = fetch_all_sources()
    briefing = generate_brief(articles, markets)
    
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "markets": markets,
        "briefing": briefing
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("✅ data.json güncellendi!")

if __name__ == "__main__":
    main()
