import json
import urllib.request
import urllib.parse
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://www.carrefour.fr/",
    "Origin": "https://www.carrefour.fr",
}

# Liste étendue de mots-clés pour balayer TOUT le magasin
MOTS_CLES_EXHAUSTIFS = [
    # 🥩 Boucherie & Charcuterie
    "poulet", "dinde", "steak hache", "boeuf", "porc", "jambon", "lardons", "saucisse", "escalope",
    
    # 🐟 Poissonnerie
    "saumon", "cabillaud", "thon", "crevettes", "colin",
    
    # 🥦 Fruits & Légumes
    "pomme de terre", "carotte", "oignon", "courgette", "poivron", "tomate", "salade", "brocoli", "champignon", "avocat",
    
    # 🍝 Féculents & Épicerie
    "pates", "penne", "spaghetti", "riz", "semoule", "lentilles", "haricots rouges", "quinoa", "purée",
    
    # 🧀 Produits Laitiers & Œufs
    "oeufs", "lait", "beurre", "creme fraiche", "emmental", "mozzarella", "fromage râpé", "camembert", "yaourt",
    
    # 🥫 Épicerie fine & Sauces
    "sauce tomate", "pesto", "huile d olive", "farine", "sucre", "conserves", "maïs", "petits pois",
    
    # 🧊 Surgelés
    "poelee", "pizza", "poisson pane", "frites"
]

def chercher_produits(recherche):
    """Récupère jusqu'à 12 articles par recherche."""
    url = f"https://www.carrefour.fr/api/search?q={urllib.parse.quote(recherche)}&page=1"
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            produits = []
            
            # On prend jusqu'à 12 articles par catégorie
            for item in data.get("data", [])[:12]:
                attrs = item.get("attributes", {})
                title = attrs.get("title")
                price = attrs.get("price", {}).get("perUnit")
                slug = attrs.get("slug", "")
                
                if title and price:
                    produits.append({
                        "item": title,
                        "prix": float(price),
                        "cat": "Carrefour Drive",
                        "url": f"https://www.carrefour.fr/p/{slug}" if slug else "https://www.carrefour.fr"
                    })
            return produits
    except Exception as e:
        return []

def generer_catalogue():
    print("🚀 Lancement du balayage complet du magasin...")
    
    catalogue = []
    produits_vignes = set() # Pour éviter les doublons
    
    for i, kw in enumerate(MOTS_CLES_EXHAUSTIFS, 1):
        resultats = chercher_produits(kw)
        nouveaux = 0
        
        for p in resultats:
            # On vérifie que le produit n'est pas déjà dans la liste
            if p["item"] not in produits_vignes:
                produits_vignes.add(p["item"])
                catalogue.append(p)
                nouveaux += 1
                
        print(f"[{i}/{len(MOTS_CLES_EXHAUSTIFS)}] '{kw}' ➔ {nouveaux} nouveaux produits ajoutés.")
        time.sleep(0.3) # Petite pause rapide pour la stabilité
        
    print(f"\n📊 TOTAL : {len(catalogue)} produits uniques récupérés !")

    # Sauvegarde dans le fichier JSON
    with open("produits_locaux.json", "w", encoding="utf-8") as f:
        json.dump(catalogue, f, ensure_ascii=False, indent=2)
        
    print("✅ Le fichier 'produits_locaux.json' a été mis à jour avec succès.")

if __name__ == "__main__":
    generer_catalogue()
