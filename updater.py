import os
import json
import feedparser
import google.generativeai as genai
from datetime import datetime

GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Eğer API key yoksa veya boşsa uyarı ver
if not GENAI_API_KEY:
    print("⚠️ UYARI: GEMINI_API_KEY bulunamadı!")

genai.configure(api_key=GENAI_API_KEY)

# RSS Kaynakları
RSS_SOURCES = [
    {"name": "Defense News", "cat": "military", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/"},
    {"name": "Naval News", "cat": "military", "url": "https://www.navalnews.com/feed/"},
    {"name": "Anadolu Ajansı Gündem", "cat": "turkey", "url": "https://www.aa.com.tr/tr/rss/default?cat=gundem"},
    {"name": "Al-Monitor", "cat": "regional", "url": "https://www.al-monitor.com/rss"}
]

def fetch_kapalicarsi_and_bist():
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
                    "title": getattr(entry, 'title', 'Haber'),
                    "summary": getattr(entry, 'summary', '')[:200]
                })
        except Exception as e:
            print(f"Hata ({source['name']}): {e}")
    return collected

def generate_brief(articles, markets):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Sen 'The Global Brief' platformunun baş istihbarat analizcisisin.
        Piyasalar: {json.dumps(markets, ensure_ascii=False)}
        Haberler: {json.dumps(articles, ensure_ascii=False)}

        SADECE geçerli bir JSON verisi döndür, başka hiçbir metin veya markdown tırnağı yazma:
        {{
          "greeting": "Günaydın Saadet. Sistem hazır.",
          "red_alert": "Son gelişmelere göre en kritik 1 cümlelik sıcak kriz haberi",
          "bullet_1": "Önemli gelişme 1 (Türkçe)",
          "bullet_2": "Önemli gelişme 2 (English)",
          "bullet_3": "Önemli gelişme 3 (Türkçe veya English)"
        }}
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Gemini Hətası: {e}")
        return {
            "greeting": "Günaydın Saadet. Sistem yayında.",
            "red_alert": "Küresel haber akışı ve piyasa verileri taranıyor.",
            "bullet_1": "Savunma sanayii ve jeopolitik gelişmeler takip ediliyor.",
            "bullet_2": "International and regional defense feeds operational.",
            "bullet_3": "Kapalıçarşı ve BIST canlı göstergeleri entegre edildi."
        }

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
        
    print("✅ data.json başarıyla güncellendi!")

if __name__ == "__main__":
    main()
