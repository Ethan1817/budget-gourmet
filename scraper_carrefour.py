import asyncio
import json
from playwright.async_api import async_playwright

# Mots-clés enrichis (sans aucun poisson ni fruit de mer)
MOTS_CLES = [
    # Protéines (Viandes, charcuterie & alternatives)
    "poulet", "escalope dinde", "steak hache", "viande hachee", "jambon", 
    "lardons", "saucisse", "pois chiches", "haricots rouges",
    
    # Féculents, céréales & féculents doux
    "pates penne", "spaghetti", "coquillettes", "riz basmati", "riz thai", 
    "lentilles vertes", "lentilles corail", "semoule", "gnocchi", "tortilla wrap", 
    "patate douce", "pomme de terre",
    
    # Légumes
    "carottes", "oignons", "courgettes", "tomates", "salade", "poivrons", 
    "champignons", "brocoli", "haricots verts", "epinards", "ail", "mais", "poelee legumes",
    
    # Crémerie & Fromages
    "oeufs", "lait", "beurre", "emmental rape", "mozzarella", "creme fraiche", 
    "feta", "parmesan", "cheddar",
    
    # Épicerie, sauces & condiments
    "sauce tomate", "pesto", "lait de coco", "curry", "moutarde", 
    "huile d olive", "sauce soja", "cube bouillon"
]

async def recuperer_prix_carrefour():
    print("🌐 Lancement du scraper Carrefour Market...")
    catalogue = []
    produits_vus = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("⏳ Connexion à Carrefour.fr...")
        await page.goto("https://www.carrefour.fr", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        for index, kw in enumerate(MOTS_CLES, 1):
            try:
                print(f"[{index}/{len(MOTS_CLES)}] Recherche : '{kw}'...")
                url = f"https://www.carrefour.fr/s?q={kw}"
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)

                articles = await page.evaluate('''() => {
                    const items = [];
                    const cards = document.querySelectorAll('article, [data-testid="product-card"]');
                    cards.forEach((card, idx) => {
                        if (idx < 3) {
                            const titleEl = card.querySelector('h2, [class*="title"]');
                            const priceEl = card.querySelector('[class*="price"]');
                            if (titleEl && priceEl) {
                                items.push({
                                    title: titleEl.innerText.trim(),
                                    price: priceEl.innerText.trim()
                                });
                            }
                        }
                    });
                    return items;
                }''')

                count = 0
                for art in articles:
                    chiffres = "".join([c for c in art['price'].replace(',', '.') if c.isdigit() or c == '.'])
                    if chiffres and art['title'] not in produits_vus:
                        try:
                            prix_float = float(chiffres)
                            produits_vus.add(art['title'])
                            catalogue.append({
                                "item": art['title'],
                                "prix": prix_float,
                                "cat": "Carrefour Market",
                                "url": f"https://www.carrefour.fr/s?q={kw}"
                            })
                            count += 1
                        except ValueError:
                            pass

                print(f"   ↳ {count} produits ajoutés")

            except Exception as e:
                print(f"⚠️ Erreur pour '{kw}': {e}")

        await browser.close()

    if catalogue:
        with open("produits_locaux.json", "w", encoding="utf-8") as f:
            json.dump(catalogue, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 Terminé ! {len(catalogue)} produits enregistrés dans 'produits_locaux.json'.")

if __name__ == "__main__":
    asyncio.run(recuperer_prix_carrefour())