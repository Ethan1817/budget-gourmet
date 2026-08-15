import streamlit as st
import json
import os
from openai import OpenAI

st.set_page_config(page_title="BudgetGourmet IA - Carrefour Market", page_icon="🛒", layout="wide")

# Initialisation du client OpenAI (mets ta clé dans st.secrets ou variable d'environnement)
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

@st.cache_data
def charger_produits():
    if os.path.exists("produits_locaux.json"):
        with open("produits_locaux.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Chargement du catalogue
produits = charger_produits()

st.title("🤖 Générateur de Recettes & Macros par IA")
st.caption("Recettes basées sur les produits disponibles chez Carrefour Market")

# Barre latérale : Paramètres de l'IA
st.sidebar.header("🎯 Préférences")
objectif = st.sidebar.selectbox("Objectif nutritionnel", ["Prise de masse (Riche en protéines)", "Sèche / Maintien (Équilibré)", "Économique & Rapide"])
nb_recettes = st.sidebar.slider("Nombre de recettes à générer", 1, 5, 3)

def generer_recettes_avec_ia(liste_produits, objectif, count):
    # Extrait uniquement les noms et prix pour alléger le prompt
    ingredients_dispo = [f"{p['item']} ({p['prix']}€)" for p in liste_produits[:40]]
    
    prompt = f"""
    Tu es un chef cuisinier et nutritionniste.
    Voici la liste des produits disponibles chez Carrefour Market avec leurs prix :
    {json.dumps(ingredients_dispo, ensure_ascii=False)}

    Génère {count} recettes uniques adaptées à l'objectif : '{objectif}'.
    Attention : pas de poisson ni fruits de mer.

    Réponds STRICTEMENT au format JSON avec cette structure exacte :
    [
      {{
        "nom": "Nom de la recette",
        "temps": "20 min",
        "prix_estime": 3.50,
        "ingredients": ["Ingrédient 1", "Ingrédient 2"],
        "instructions": "Étape 1: ... Étape 2: ...",
        "macros": {{
          "calories": 500,
          "proteines": 40,
          "glucides": 50,
          "lipides": 10
        }}
      }}
    ]
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"} if hasattr(client.chat.completions, 'response_format') else None
    )
    
    contenu = response.choices[0].message.content
    # Si le retour est enrobé dans un dictionnaire principal JSON
    data = json.loads(contenu)
    return data if isinstance(data, list) else data.get("recettes", data.get("data", []))

# Bouton de génération
if not api_key:
    st.warning("🔑 Veuillez renseigner votre clé API OpenAI dans un fichier `.env` ou `.streamlit/secrets.toml` pour activer la génération.")
else:
    if st.button("🚀 Générer mes recettes avec les prix en direct", type="primary"):
        with st.spinner("L'IA concocte vos recettes et calcule les macros..."):
            try:
                recettes_ia = generer_recettes_avec_ia(produits, objectif, nb_recettes)
                st.session_state["recettes_ia"] = recettes_ia
            except Exception as e:
                st.error(f"Erreur lors de la génération par l'IA : {e}")

# Affichage des recettes générées
if "recettes_ia" in st.session_state:
    for recette in st.session_state["recettes_ia"]:
        with st.expander(f"📖 **{recette['nom']}** — ~{recette.get('prix_estime', 0):.2f} € ({recette.get('temps', '15 min')})", expanded=True):
            
            st.write("**Ingrédients :** " + ", ".join(recette.get('ingredients', [])))
            st.write("**Préparation :** " + recette.get('instructions', ''))
            
            st.markdown("---")
            st.caption("📊 **Macronutriments (par portion) :**")
            
            macros = recette.get('macros', {})
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🔥 Calories", f"{macros.get('calories', 0)} kcal")
            col2.metric("🍗 Protéines", f"{macros.get('proteines', 0)} g")
            col3.metric("🌾 Glucides", f"{macros.get('glucides', 0)} g")
            col4.metric("🥑 Lipides", f"{macros.get('lipides', 0)} g")
            st.checkbox(f"**{row['item']}** — {row['prix']:.2f} € *({row['cat']})*", key=f"item_{idx}")
