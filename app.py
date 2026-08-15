import streamlit as st
import json
import os
from groq import Groq

st.set_page_config(page_title="BudgetGourmet IA - Carrefour Market", page_icon="🛒", layout="wide")

# --- Gestion de la clé API Groq ---
api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
elif os.getenv("GROQ_API_KEY"):
    api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key) if api_key else None

# --- Chargement des produits ---
@st.cache_data
def charger_produits():
    if os.path.exists("produits_locaux.json"):
        try:
            with open("produits_locaux.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erreur de lecture du fichier JSON : {e}")
            return []
    return []

produits = charger_produits()

# --- Interface Utilisateur ---
st.title("🤖 Générateur de Recettes & Macros par IA")
st.caption("Recettes gratuites basées sur les produits disponibles chez Carrefour Market")

if not produits:
    st.info("ℹ️ Aucun produit trouvé dans `produits_locaux.json` ou le fichier n'est pas encore présent sur GitHub.")

st.sidebar.header("🎯 Préférences")
objectif = st.sidebar.selectbox("Objectif nutritionnel", ["Prise de masse (Riche en protéines)", "Sèche / Maintien (Équilibré)", "Économique & Rapide"])
nb_recettes = st.sidebar.slider("Nombre de recettes à générer", 1, 5, 3)

def generer_recettes_avec_ia(liste_produits, objectif, count):
    ingredients_dispo = [f"{p.get('item', '')} ({p.get('prix', '')}€)" for p in liste_produits[:40]] if liste_produits else ["Poulet", "Riz", "Légumes", "Œufs"]
    
    prompt = f"""
    Tu es un chef cuisinier et nutritionniste.
    Voici des exemples de produits disponibles chez Carrefour Market avec leurs prix :
    {json.dumps(ingredients_dispo, ensure_ascii=False)}

    Génère {count} recettes uniques adaptées à l'objectif : '{objectif}'.
    Attention : STRICTEMENT AUCUN POISSON NI FRUIT DE MER.

    Réponds STRICTEMENT sous forme d'un objet JSON valide contenant une liste "recettes" avec ce format :
    {{
      "recettes": [
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
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    contenu = response.choices[0].message.content
    data = json.loads(contenu)
    return data.get("recettes", [])

# Vérification de la clé API
if not api_key:
    st.error("🔑 Clé API Groq introuvable. Veuillez ajouter `GROQ_API_KEY` dans les **Secrets** de Streamlit (Settings ⚙️ -> Secrets).")
else:
    if st.button("🚀 Générer mes recettes avec les prix en direct", type="primary"):
        with st.spinner("L'IA (Groq) concocte vos recettes et calcule les macros..."):
            try:
                recettes_ia = generer_recettes_avec_ia(produits, objectif, nb_recettes)
                st.session_state["recettes_ia"] = recettes_ia
            except Exception as e:
                st.error(f"Erreur lors de la génération par l'IA : {e}")

# Affichage des recettes
if "recettes_ia" in st.session_state:
    for recette in st.session_state["recettes_ia"]:
        with st.expander(f"📖 **{recette.get('nom', 'Recette')}** — ~{recette.get('prix_estime', 0):.2f} € ({recette.get('temps', '15 min')})", expanded=True):
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
