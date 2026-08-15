import json
import os
import urllib.parse
from groq import Groq
import streamlit as st

# Configuration de la page
st.set_page_config(page_title="BudgetGourmet IA", page_icon="🍳", layout="wide")

# --- CSS Personnalisé ---
st.markdown(
    """
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .recipe-card {
        background: linear-gradient(145deg, #1E222B, #17191E);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 20px;
        border: 1px solid #2D3139;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        transition: all 0.3s ease;
    }
    .recipe-card:hover {
        transform: translateY(-4px);
        border-color: #FF4B4B;
        box-shadow: 0 12px 28px rgba(255, 75, 75, 0.2);
    }
    .badge-price {
        background-color: #10B981;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85em;
    }
    .badge-time {
        background-color: #374151;
        color: #E5E7EB;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.85em;
    }
    .badge-macro {
        background-color: #1F2937;
        color: #9CA3AF;
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 0.8em;
        margin-right: 4px;
        border: 1px solid #374151;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- Initialisation API Groq ---
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


# --- Chargement des produits locaux ---
@st.cache_data
def charger_produits():
    if os.path.exists("produits_locaux.json"):
        try:
            with open("produits_locaux.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


produits = charger_produits()

# --- Barre latérale ---
st.sidebar.title("🎛️ Configuration")
objectif = st.sidebar.selectbox(
    "Objectif nutritionnel",
    [
        "Prise de masse (Protéiné)",
        "Sèche / Maintien (Équilibré)",
        "Économique & Rapide",
    ],
)
nb_repas = st.sidebar.slider("Nombre de repas à planifier", 1, 30, 7)
budget_max = st.sidebar.number_input(
    "Budget total max (€)",
    min_value=5.0,
    max_value=500.0,
    value=50.0,
    step=5.0,
)

st.sidebar.markdown("---")
st.sidebar.subheader("🧊 Anti-Gaspillage / Vide-Frigo")
vide_frigo = st.sidebar.text_input(
    "Ingrédients à utiliser en priorité",
    placeholder="Ex: Œufs, Riz, Tomates...",
)

st.sidebar.info(f"💡 Budget cible : **{budget_max/nb_repas:.2f} €** / repas")


# --- Fonctions IA ---
def generer_menu_ia(liste_produits, objectif, count, budget, frigo=""):
    ingredients_dispo = (
        [f"{p.get('item', '')} ({p.get('prix', '')}€)" for p in liste_produits[:50]]
        if liste_produits
        else ["Poulet", "Riz", "Légumes", "Œufs"]
    )

    prompt = f"""
    Tu es un chef cuisinier et nutritionniste expert.
    Génère un plan de {count} repas uniques respectant un budget TOTAL maximum de {budget} € (soit ~{budget/count:.2f} € par repas).
    Objectif : '{objectif}'.
    Ingrédients déjà disponibles au frigo : '{frigo}'.
    Exemples de produits Carrefour disponibles : {json.dumps(ingredients_dispo, ensure_ascii=False)}

    RÈGLES STRICTES :
    - STRICTEMENT AUCUN POISSON NI FRUIT DE MER.
    - Mot-clé anglais ("keyword_photo") représentant visuellement le plat pour récupérer une image culinaire (ex: burger, pasta, chicken, salad, steak).

    Réponds STRICTEMENT avec un objet JSON valide suivant ce format :
    {{
      "recettes": [
        {{
          "id": 1,
          "nom": "Nom gourmand du plat",
          "keyword_photo": "chicken",
          "temps": "20 min",
          "prix_estime": 3.20,
          "ingredients": [
            {{"nom": "Blanc de poulet 300g", "rayon": "Boucherie", "recherche_carrefour": "blanc de poulet"}},
            {{"nom": "Riz basmati 500g", "rayon": "Épicerie", "recherche_carrefour": "riz basmati"}}
          ],
          "instructions": "1. Saisir le poulet... 2. Cuire le riz...",
          "macros": {{"calories": 600, "proteines": 45, "glucides": 60, "lipides": 12}}
        }}
      ]
    }}
    """

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(res.choices[0].message.content).get("recettes", [])


def remplacer_une_recette(recette_ancienne, objectif, budget_cible):
    prompt = f"""
    Propose un NOUVEAU plat unique pour remplacer '{recette_ancienne.get('nom')}'.
    Prix cible : ~{budget_cible:.2f} €.
    Objectif : '{objectif}'.
    STRICTEMENT AUCUN POISSON NI FRUIT DE MER.

    Réponds au format JSON strict :
    {{
      "nom": "Nouveau plat gourmand",
      "keyword_photo": "pasta",
      "temps": "15 min",
      "prix_estime": {budget_cible},
      "ingredients": [
        {{"nom": "Pâtes 500g", "rayon": "Épicerie", "recherche_carrefour": "pates"}}
      ],
      "instructions": "1. Cuire les pâtes...",
      "macros": {{"calories": 550, "proteines": 30, "glucides": 70, "lipides": 10}}
    }}
    """

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(res.choices[0].message.content)


# --- En-tête Principal ---
st.title("🍳 BudgetGourmet IA")
st.caption(
    "Planification de repas sur-mesure, anti-gaspillage, planning hebdomadaire et liens Carrefour."
)

if not api_key:
    st.error("🔑 Veuillez ajouter la clé `GROQ_API_KEY` dans vos Secrets Streamlit.")
else:
    if st.button("✨ Générer mon menu personnalisé", type="primary", use_container_width=True):
        with st.spinner("L'IA prépare vos recettes et calcule les dépenses..."):
            try:
                st.session_state["menu"] = generer_menu_ia(
                    produits, objectif, nb_repas, budget_max, vide_frigo
                )
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")

# --- Affichage des résultats ---
if "menu" in st.session_state and st.session_state["menu"]:
    recettes = st.session_state["menu"]
    cout_total = sum(r.get("prix_estime", 0) for r in recettes)

    st.markdown("---")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric(
        "Total estimé",
        f"{cout_total:.2f} €",
        delta=f"{budget_max - cout_total:.2f} € de marge",
    )
    col_b.metric("Plats planifiés", f"{len(recettes)} repas")
    col_c.metric("Moyenne / repas", f"{cout_total/len(recettes):.2f} €")

    tab_menu, tab_planning, tab_courses = st.tabs(
        ["🍽️ Catalogue de Repas", "📅 Planning Semaine", "🛒 Liste de Courses Globale"]
    )

    with tab_menu:
        cols = st.columns(3)
        for idx, r in enumerate(recettes):
            with cols[idx % 3]:
                keyword = r.get("keyword_photo", "food")
                img_url = f"https://loremflickr.com/600/400/{urllib.parse.quote(keyword)}?lock={idx}"

                st.image(img_url, use_column_width=True)
                st.markdown(f"### {r.get('nom')}")
                st.markdown(
                    f"<span class='badge-price'>💰 ~{r.get('prix_estime', 0):.2f} €</span> "
                    f"<span class='badge-time'>⏱️ {r.get('temps')}</span>",
                    unsafe_allow_html=True,
                )

                macros = r.get("macros", {})
                st.markdown(
                    f"""
                <div style='margin-top:8px; margin-bottom:12px;'>
                    <span class='badge-macro'>🔥 {macros.get('calories',0)} kcal</span>
                    <span class='badge-macro'>🍗 {macros.get('proteines',0)}g Prot</span>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if st.button(f"🔄 Changer ce plat", key=f"swap_{idx}"):
                    with st.spinner("Recherche d'une alternative..."):
                        nouvelle_recette = remplacer_une_recette(
                            r, objectif, budget_max / len(recettes)
                        )
                        st.session_state["menu"][idx] = nouvelle_recette
                        st.rerun()

                with st.expander("📖 Voir la recette complète & liens Carrefour"):
                    st.markdown("#### 🛒 Ingrédients :")
                    for ing in r.get("ingredients", []):
                        nom_ing = ing.get("nom", ing) if isinstance(ing, dict) else ing
                        query = (
                            ing.get("recherche_carrefour", nom_ing)
                            if isinstance(ing, dict)
                            else nom_ing
                        )
                        link = f"https://www.carrefour.fr/s?q={urllib.parse.quote(query)}"
                        st.markdown(f"- **{nom_ing}** ➔ [Acheter sur Carrefour.fr 🔗]({link})")

                    st.markdown("#### 👨‍🍳 Instructions :")
                    st.write(r.get("instructions"))

                    st.markdown("#### 📊 Macros détaillés :")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("🔥 Calories", f"{macros.get('calories', 0)}")
                    col2.metric("🍗 Protéines", f"{macros.get('proteines', 0)} g")
                    col3.metric("🍞 Glucides", f"{macros.get('glucides', 0)} g")
                    col4.metric("🥑 Lipides", f"{macros.get('lipides', 0)} g")

    with tab_planning:
        st.subheader("📅 Votre planning de repas")
        jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

        for idx, r in enumerate(recettes):
            jour = jours[idx % 7]
            moment = "Déjeuner" if (idx // 7) % 2 == 0 else "Dîner"
            st.markdown(
                f"**{jour} ({moment})** : {r.get('nom')} — *~{r.get('prix_estime',0):.2f} €*"
            )

    with tab_courses:
        st.subheader("📋 Liste de courses consolidée par rayon")

        liste_rayons = {}
        for r in recettes:
            for ing in r.get("ingredients", []):
                if isinstance(ing, dict):
                    rayon = ing.get("rayon", "Autre")
                    nom = ing.get("nom")
                else:
                    rayon = "Autre"
                    nom = ing

                if rayon not in liste_rayons:
                    liste_rayons[rayon] = []
                liste_rayons[rayon].append(nom)

        texte_export = (
            f"LISTE DE COURSES - BUDGETGOURMET ({len(recettes)} repas)\n"
            f"Total estimé : {cout_total:.2f} €\n\n"
        )

        for rayon, items in liste_rayons.items():
            st.markdown(f"#### 📦 {rayon}")
            texte_export += f"--- {rayon} ---\n"
            for item in set(items):
                st.write(f"- [ ] {item}")
                texte_export += f"- {item}\n"
            texte_export += "\n"

        st.download_button(
            label="📥 Télécharger la liste de courses (.txt)",
            data=texte_export,
            file_name="liste_de_courses_budgetgourmet.txt",
            mime="text/plain",
        )
