def generer_menu_ia(liste_produits, objectif, count, budget, frigo=""):
    ingredients_dispo = (
        [f"{p.get('item', '')} ({p.get('prix', '')}€)" for p in liste_produits[:30]]
        if liste_produits
        else ["Poulet", "Riz", "Légumes", "Œufs", "Pâtes", "Bœuf"]
    )

    prompt = f"""
    Tu es un assistant culinaire étudiant.
    Génère EXACTEMENT un tableau de {count} repas étudiants simples, rapides (15-20 min max) et pas chers.
    Budget TOTAL max : {budget} € (soit ~{budget/count:.2f} € par repas).
    Objectif : '{objectif}'.
    Ingrédients frigo à intégrer si possible : '{frigo}'.
    Exemples d'ingrédients Carrefour : {json.dumps(ingredients_dispo, ensure_ascii=False)}

    RÈGLES IMPÉRATIVES :
    1. Le tableau "recettes" doit contenir STRICTEMENT {count} éléments.
    2. Recettes simples et gourmandes. STRICTEMENT AUCUN POISSON NI FRUIT DE MER.
    3. "categorie_photo" doit être STRICTEMENT un mot parmi : ["pasta", "chicken", "burger", "wrap", "tacos", "rice", "curry", "salad", "pizza", "eggs", "steak", "noodles", "sandwich"].

    Format JSON attendu :
    {{
      "recettes": [
        {{
          "id": 1,
          "nom": "Wrap Poulet Épicé",
          "categorie_photo": "wrap",
          "temps": "15 min",
          "prix_estime": 2.80,
          "ingredients": [
            {{"nom": "Tortillas de blé (x4)", "rayon": "Épicerie du monde", "recherche_carrefour": "tortillas"}},
            {{"nom": "Émincé de poulet 200g", "rayon": "Boucherie", "recherche_carrefour": "poulet"}}
          ],
          "instructions": "Faire griller le poulet avec des épices, garnir la tortilla et réchauffer.",
          "macros": {{"calories": 520, "proteines": 38, "glucides": 50, "lipides": 14}}
        }}
      ]
    }}
    """

    # Utilisation de llama-3.1-8b-instant pour éviter la limite de quota
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=8000,
        )
    except Exception:
        # Fallback automatique sur llama3-8b-8192 si besoin
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=8000,
        )

    return json.loads(res.choices[0].message.content).get("recettes", [])


def remplacer_une_recette(recette_ancienne, objectif, budget_cible):
    prompt = f"""
    Génère 1 seul plat étudiant simple et gourmand pour remplacer '{recette_ancienne.get('nom')}'.
    Budget cible : ~{budget_cible:.2f} €. Objectif : '{objectif}'.
    STRICTEMENT AUCUN POISSON NI FRUIT DE MER.
    "categorie_photo" parmi : ["pasta", "chicken", "burger", "wrap", "tacos", "rice", "curry", "salad", "pizza", "eggs", "steak", "noodles", "sandwich"].

    JSON strict :
    {{
      "nom": "Pâtes crémeuses au poulet",
      "categorie_photo": "pasta",
      "temps": "15 min",
      "prix_estime": {budget_cible},
      "ingredients": [
        {{"nom": "Penne 500g", "rayon": "Épicerie", "recherche_carrefour": "penne"}},
        {{"nom": "Crème fraîche 20cl", "rayon": "Crémerie", "recherche_carrefour": "creme fraiche"}}
      ],
      "instructions": "Cuire les pâtes. Mélanger la crème avec le poulet.",
      "macros": {{"calories": 550, "proteines": 35, "glucides": 65, "lipides": 12}}
    }}
    """

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=1000,
    )
    return json.loads(res.choices[0].message.content)
