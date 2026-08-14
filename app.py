import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="BudgetGourmet - Générateur de repas",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé pour un rendu professionnel
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #2b8a3e; color: white; border-radius: 8px; font-weight: bold; }
    .metric-card { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

st.title("🛒 BudgetGourmet — Assistant Repas & Courses")
st.caption("Planifiez vos repas pour 1 personne selon votre enseigne et votre budget exact.")

# --- BARRE LATÉRALE : PARAMÈTRES ---
with st.sidebar:
    st.header("⚙️ Vos Paramètres")
    
    enseigne = st.selectbox(
        "Choisissez votre enseigne :",
        ["Carrefour Market", "Carrefour City", "Lidl"]
    )
    
    budget = st.number_input("Budget maximum (€) :", min_value=10, max_value=500, value=50, step=5)
    duree_jours = st.slider("Durée (jours) :", min_value=1, max_value=14, value=7)
    
    st.subheader("🥗 Catégories de plats")
    cat_rapide = st.checkbox("Rapide & Facile (< 15 min)", value=True)
    cat_proteine = st.checkbox("Riche en Protéines", value=True)
    cat_economique = st.checkbox("Ultra Économique", value=True)
    cat_vege = st.checkbox("Végétarien", value=False)
    
    btn_generer = st.button("🚀 Générer mon menu & mes courses")

# --- BASE DE DONNÉES SIMULÉE DES INGRÉDIENTS PAR ENSEIGNE ---
BASE_PRODUITS = {
    "Lidl": [
        {"item": "Filet de Poulet 500g", "prix": 4.50, "cat": "Protéines"},
        {"item": "Pâtes Penne 1kg", "prix": 1.15, "cat": "Féculents"},
        {"item": "Riz Basmati 1kg", "prix": 1.80, "cat": "Féculents"},
        {"item": "Œufs Plein Air (x10)", "prix": 2.20, "cat": "Protéines"},
        {"item": "Légumes Poêlée Surgelée 1kg", "prix": 2.10, "cat": "Légumes"},
        {"item": "Sauce Tomate Basilic 400g", "prix": 0.95, "cat": "Épicerie"},
        {"item": "Fromage Râpé 200g", "prix": 1.60, "cat": "Crémerie"},
    ],
    "Carrefour Market": [
        {"item": "Filet de Poulet Carrefour 500g", "prix": 4.90, "cat": "Protéines"},
        {"item": "Pâtes Penne Barilla 500g", "prix": 1.25, "cat": "Féculents"},
        {"item": "Riz Basmati Carrefour 1kg", "prix": 1.95, "cat": "Féculents"},
        {"item": "Œufs Carrefour Bio (x6)", "prix": 2.10, "cat": "Protéines"},
        {"item": "Mélange Légumes Carrefour 750g", "prix": 2.40, "cat": "Légumes"},
        {"item": "Sauce Tomate Panzani 400g", "prix": 1.35, "cat": "Épicerie"},
        {"item": "Emmental Râpé Président 200g", "prix": 2.10, "cat": "Crémerie"},
    ],
    "Carrefour City": [
        {"item": "Filet de Poulet 400g", "prix": 5.20, "cat": "Protéines"},
        {"item": "Pâtes Penne 500g", "prix": 1.40, "cat": "Féculents"},
        {"item": "Riz Basmati 500g", "prix": 1.60, "cat": "Féculents"},
        {"item": "Œufs Plein Air (x6)", "prix": 2.30, "cat": "Protéines"},
        {"item": "Légumes Frais Poivrons/Oignons 400g", "prix": 2.80, "cat": "Légumes"},
        {"item": "Sauce Tomate Saclà 190g", "prix": 1.80, "cat": "Épicerie"},
        {"item": "Emmental Râpé 150g", "prix": 1.90, "cat": "Crémerie"},
    ]
}

# --- AFFICHAGE ET LOGIQUE PRINCIPALE ---
if btn_generer or "menu_genere" in st.session_state:
    st.session_state["menu_genere"] = True
    
    produits = BASE_PRODUITS.get(enseigne, BASE_PRODUITS["Carrefour Market"])
    df_produits = pd.DataFrame(produits)
    total_estime = df_produits["prix"].sum()
    
    # KPIs / En-tête métrique
    col1, col2, col3 = st.columns(3)
    col1.metric("Magasin sélectionné", enseigne)
    col2.metric("Budget Alloué", f"{budget:.2f} €")
    col3.metric("Total Panier Estimé", f"{total_estime:.2f} €", delta=f"{budget - total_estime:.2f} € restant")

    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🍲 Menu & Recettes de la Semaine", "🛒 Liste de Courses"])
    
    with tab1:
        st.subheader(f"Planning des repas pour {duree_jours} jours (1 Personne)")
        for jour in range(1, duree_jours + 1):
            with st.expander(f"📅 Jour {jour} — Poêlée de Poulet & Riz aux Légumes"):
                st.markdown("""
                * **Type de plat :** Rapide & Protéiné
                * **Temps de préparation :** 12 minutes
                * **Coût estimé du plat :** ~ 2,80 € / portion
                
                **Ingrédients nécessaires :**
                * 120g de Filet de Poulet
                * 80g de Riz Basmati
                * 150g de Poêlée de Légumes
                
                **Préparation :**
                1. Faire cuire le riz basmati dans de l'eau bouillante salée (10 min).
                2. Dans une poêle avec un filet d'huile d'olive, faire revenir le poulet coupé en dés.
                3. Ajouter les légumes et laisser mijoter 5 minutes à feu moyen. Mélanger au riz et servir chaud.
                """)

    with tab2:
        st.subheader("Liste de courses à cocher en magasin")
        st.info("Cochez les articles au fur et à mesure que vous les mettez dans votre chariot.")
        
        for idx, row in df_produits.iterrows():
            st.checkbox(f"**{row['item']}** — {row['prix']:.2f} € *({row['cat']})*", key=f"item_{idx}")