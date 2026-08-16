import json
import os
import urllib.parse
from groq import Groq
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="BudgetGourmet IA",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Banque d'images HD par catégorie ---
BANQUE_IMAGES = {
    "pasta": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=600&q=80",
    "chicken": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=600&q=80",
    "burger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80",
    "wrap": "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80",
    "tacos": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=600&q=80",
    "rice": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=600&q=80",
    "curry": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80",
    "salad": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80",
    "pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80",
    "eggs": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=600&q=80",
    "steak": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80",
    "noodles": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80",
    "sandwich": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=600&q=80",
    "default": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
}

# --- CSS Thème Gastronomique Sombre & Ambré ---
st.markdown(
    """
<style>
    .stApp {
        background-color: #0F0E0E;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    div[data-testid="stSidebar"] {
        background-color: #161515;
        border-right: 1px solid #2A2828;
    }
    .main-header {
        font-size: 2.6rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
    }
    .main-header span {
        color: #E07A5F;
    }
    .badge-price {
        background-color: #E07A5F;
        color: #FFFFFF;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-time {
        background-color: #262424;
        color: #D1D5DB;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        border: 1px solid #3A3636;
        display: inline-block;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #181717 !important;
        border: 1px solid #2D2B2B !important;
        border-radius: 12px !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #E07A5F !important;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    button[kind="primary"] {
        background-color: #E07A5F !important;
        border: none !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #C8634B !important;
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

# --- Sidebar : Configuration ---
st.sidebar.markdown("## 🎛️ Paramètres")
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
    "Budget total (€)",
    min_value=5.0,
    max_value=500.0,
    value=50.0,
    step=5.0,
)

st.sidebar.markdown("---")
vide_frigo = st.sidebar.text_input(
    "🧊 Anti-Gaspillage (Restes du frigo)",
    placeholder="Ex: Poulet, Riz, Œufs...",
)

budget_par_repas = budget_max / nb_repas
st.sidebar.info(f"💡 Budget cible : **{budget_par_repas:.2f} €** / repas")


# --- Fonctions IA ---
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
    2. Recettes simples et gourmandes (wraps, pâtes, quesadillas, riz sauté, omelette garnie, gratins). Pas de plats complexes.
    3. STRICTEMENT AUCUN POISSON NI FRUIT DE MER.
    4. "categorie_photo" doit être STRICTEMENT un mot parmi : ["pasta", "chicken", "burger", "wrap", "tacos", "rice", "curry", "salad", "pizza", "eggs", "steak", "noodles", "sandwich"].

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

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=8000,
        )
    except Exception:
        # Secours sur le modèle 70b actif si le 8b rencontre un souci
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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


# --- En-tête Principal ---
st.markdown(
    '<p class="main-header">🍳 Budget<span>Gourmet</span> IA</p>',
    unsafe_allow_html=True,
)
st.caption(
    "Planificateur de repas étudiants : recettes gourmandes, rapides et adaptées à ton budget."
)

if not api_key:
    st.error("🔑 Veuillez configurer la clé `GROQ_API_KEY` dans vos Secrets Streamlit.")
else:
    if st.button(
        f"✨ Générer mes {nb_repas} repas", type="primary", use_container_width=True
    ):
        with st.spinner(f"Génération de vos {nb_repas} repas en cours..."):
            try:
                st.session_state["menu"] = generer_menu_ia(
                    produits, objectif, nb_repas, budget_max, vide_frigo
                )
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")

# --- Affichage des Résultats ---
if "menu" in st.session_state and st.session_state["menu"]:
    recettes = st.session_state["menu"]
    cout_total = sum(r.get("prix_estime", 0) for r in recettes)

    st.markdown("---")

    # Métriques
    m1, m2, m3 = st.columns(3)
    m1.metric("Budget total", f"{cout_total:.2f} €", f"{budget_max - cout_total:.2f} € de marge")
    m2.metric("Repas générés", f"{len(recettes)} / {nb_repas}")
    m3.metric("Prix moyen / repas", f"{(cout_total/len(recettes)) if recettes else 0:.2f} €")

    tab_menu, tab_planning, tab_courses = st.tabs(
        ["🍽️ Catalogue des Repas", "📅 Planning de la Semaine", "🛒 Liste de Courses"]
    )

    # --- TAB 1 : CATALOGUE ---
    with tab_menu:
        cols = st.columns(3)
        for idx, r in enumerate(recettes):
            with cols[idx % 3]:
                with st.container(border=True):
                    # Sélection de l'image HD
                    cat = str(r.get("categorie_photo", "default")).lower().strip()
                    img_url = BANQUE_IMAGES.get(cat, BANQUE_IMAGES["default"])
                    
                    st.image(img_url, use_container_width=True)

                    st.markdown(f"### {r.get('nom', 'Plat')}")
                    st.markdown(
                        f"<span class='badge-price'>💰 ~{r.get('prix_estime', 0):.2f} €</span> "
                        f"<span class='badge-time'>⏱️ {r.get('temps', '15 min')}</span>",
                        unsafe_allow_html=True,
                    )

                    macros = r.get("macros", {})
                    st.caption(
                        f"🔥 {macros.get('calories', 0)} kcal | 🍗 {macros.get('proteines', 0)}g Prot | 🍞 {macros.get('glucides', 0)}g Gluc"
                    )

                    if st.button("🔄 Changer ce plat", key=f"swap_{idx}", use_container_width=True):
                        with st.spinner("Recherche d'une alternative..."):
                            st.session_state["menu"][idx] = remplacer_une_recette(
                                r, objectif, budget_max / len(recettes)
                            )
                            st.rerun()

                    with st.expander("📖 Ingrédients & Préparation"):
                        st.markdown("**🛒 Ingrédients :**")
                        for ing in r.get("ingredients", []):
                            nom_ing = ing.get("nom", ing) if isinstance(ing, dict) else ing
                            query = (
                                ing.get("recherche_carrefour", nom_ing)
                                if isinstance(ing, dict)
                                else nom_ing
                            )
                            link = f"https://www.carrefour.fr/s?q={urllib.parse.quote(query)}"
                            st.markdown(f"- **{nom_ing}** ➔ [Carrefour.fr 🔗]({link})")

                        st.markdown("**👨‍🍳 Préparation :**")
                        st.write(r.get("instructions", "Étapes non détaillées."))

    # --- TAB 2 : PLANNING ---
    with tab_planning:
        st.subheader("📅 Organisation des repas")
        jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        for idx, r in enumerate(recettes):
            jour = jours[idx % 7]
            moment = "Déjeuner" if (idx // 7) % 2 == 0 else "Dîner"
            st.write(f"**{jour} ({moment}) :** {r.get('nom')} — *~{r.get('prix_estime', 0):.2f} €*")

    # --- TAB 3 : LISTE DE COURSES ---
    with tab_courses:
        st.subheader("📋 Liste de courses regroupée")
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

        texte_export = f"LISTE DE COURSES ({len(recettes)} repas) - Total estimé : {cout_total:.2f} €\n\n"

        for rayon, items in liste_rayons.items():
            st.markdown(f"#### 📦 {rayon}")
            texte_export += f"--- {rayon} ---\n"
            for item in set(items):
                st.write(f"- [ ] {item}")
                texte_export += f"- {item}\n"
            texte_export += "\n"

        st.download_button(
            label="📥 Télécharger la liste (.txt)",
            data=texte_export,
            file_name="liste_de_courses.txt",
            mime="text/plain",
            use_container_width=True,
        )
