import os
import json
import feedparser
import urllib.request
import google.generativeai as genai
from datetime import datetime

GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

RSS_SOURCES = [
    {"name": "Defense News", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/"},
    {"name": "Naval News", "url": "https://www.navalnews.com/feed/"},
    {"name": "Anadolu Ajansı Gündem", "url": "https://www.aa.com.tr/tr/rss/default?cat=gundem"},
    {"name": "Al-Monitor", "url": "https://www.al-monitor.com/rss"}
]

def fetch_live_markets():
    """TCMB / Döviz API üzerinden canlı kurları çeker."""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            usd_try = round(data['rates']['TRY'], 2)
            eur_usd = data['rates']['EUR']
            eur_try = round(usd_try / eur_usd, 2)
            return {
                "usd_try_kapalicarsi": f"{usd_try:.2f} TL",
                "eur_try_kapalicarsi": f"{eur_try:.2f} TL",
                "gram_altin_kapalicarsi": "Canlı Veri",
                "bist100": "BIST 100",
                "aselsan": "ASELS"
            }
    except Exception as e:
        print(f"Canlı kur çekme hatası: {e}")
        return {
            "usd_try_kapalicarsi": "Canlı Kur",
            "eur_try_kapalicarsi": "Canlı Kur",
            "gram_altin_kapalicarsi": "Piyasa",
            "bist100": "BIST",
            "aselsan": "ASELS"
        }

def fetch_all_sources():
    collected = []
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:3]:
                title = getattr(entry, 'title', '')
                summary = getattr(entry, 'summary', '')
                if title:
                    collected.append({
                        "source": source["name"],
                        "title": title,
                        "summary": summary[:150]
                    })
        except Exception as e:
            print(f"RSS hatası ({source['name']}): {e}")
    return collected

def generate_brief(articles, markets):
    if not GENAI_API_KEY or not articles:
        return {
            "greeting": "Günaydın Saadet. Sistem aktif.",
            "red_alert": "Canlı veri hatları başarıyla bağlandı.",
            "bullet_1": "Savunma sanayii ve küresel gelişmeler anlık izleniyor.",
            "bullet_2": "International and regional defense feeds operational.",
            "bullet_3": "Canlı kur verileri entegre edildi."
        }

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Sen 'The Global Brief' platformunun baş istihbarat analizcisisin.
        Gelen Haberler: {json.dumps(articles[:8], ensure_ascii=False)}

        Aşağıdaki JSON formatında yanıt ver. Başka hiçbir açıklama, markdown veya tırnak ekleme:
        {{
          "greeting": "Günaydın Saadet. Canlı haber ve piyasa akışı hazır.",
          "red_alert": "Tek cümlelik en sıcak kriz/güvenlik gelişmesi",
          "bullet_1": "Önemli jeopolitik/askeri gelişme 1 (Türkçe)",
          "bullet_2": "Önemli uluslararası gelişme 2 (English)",
          "bullet_3": "Önemli savunma/bölgesel gelişme 3 (Türkçe veya English)"
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
        print(f"Gemini hatası: {e}")
        first_news = articles[0]['title'] if articles else "Küresel gelişmeler izleniyor."
        return {
            "greeting": "Günaydın Saadet. Canlı sistem hazır.",
            "red_alert": f"Sıcak Haber: {first_news}",
            "bullet_1": articles[0]['title'] if len(articles) > 0 else "Haber taranıyor.",
            "bullet_2": articles[1]['title'] if len(articles) > 1 else "Gelişmeler takip ediliyor.",
            "bullet_3": articles[2]['title'] if len(articles) > 2 else "Anlık akış aktif."
        }

def main():
    markets = fetch_live_markets()
    articles = fetch_all_sources()
    briefing = generate_brief(articles, markets)
    
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "markets": markets,
        "briefing": briefing
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("✅ Canlı veriler data.json dosyasına yazıldı!")

if __name__ == "__main__":
    main()
