import streamlit as st
import pandas as pd
import json
import os

# --- CHARGEMENT DU CATALOGUE EXHAUSTIF ---
@st.cache_data
def charger_catalogue():
    # Si le fichier généré par le scraper existe, on l'utilise
    if os.path.exists("produits_locaux.json"):
        with open("produits_locaux.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if data:
                return data
    
    # Base de secours si le fichier n'est pas encore présent
    return [
        {"item": "Filet de Poulet 500g", "prix": 4.90, "cat": "Protéines", "url": "https://www.carrefour.fr"},
        {"item": "Pâtes Penne 500g", "prix": 1.25, "cat": "Féculents", "url": "https://www.carrefour.fr"}
    ]

PRODUITS_EXACTS = charger_catalogue()