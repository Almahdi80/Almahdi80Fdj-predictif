
import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
from io import StringIO

st.set_page_config(page_title="Tableau de bord FDJ Prédictif", layout="wide")
st.title("🔮 Tableau de bord Prédictif Avancé – EuroMillions & Loto FDJ")

mot_de_passe = st.text_input("Mot de passe", type="password")
if mot_de_passe != "fdj2025":
    st.warning("Veuillez entrer le mot de passe pour accéder.")
    st.stop()

tab1, tab2 = st.tabs(["🎲 EuroMillions", "🍀 Loto FDJ"])

def score_predictif(df, colonnes, jeu_max, recent_n=100, alpha=0.4, beta=0.4, gamma=0.2):
    nums = df[colonnes]
    freq_total = nums.stack().value_counts(normalize=True)
    freq_recent = nums.tail(recent_n).stack().value_counts(normalize=True)

    co_occurrence = Counter()
    for tirage in nums.values:
        for i in range(len(tirage)):
            for j in range(i+1, len(tirage)):
                pair = tuple(sorted((tirage[i], tirage[j])))
                co_occurrence[pair] += 1

    co_scores = {}
    for n in range(1, jeu_max + 1):
        total = sum([v for (a, b), v in co_occurrence.items() if a == n or b == n])
        co_scores[n] = total / (df.shape[0] or 1)

    max_freq = max(freq_total.max(), 0.01)
    max_recent = max(freq_recent.max(), 0.01)
    max_co = max(co_scores.values()) or 1

    all_nums = sorted(set(freq_total.index.tolist() + freq_recent.index.tolist() + list(co_scores.keys())))
    scores = []
    for n in all_nums:
        f_total = freq_total.get(n, 0) / max_freq
        f_recent = freq_recent.get(n, 0) / max_recent
        f_co = co_scores.get(n, 0) / max_co
        score = alpha * f_total + beta * f_recent + gamma * f_co
        scores.append((n, round(score, 4)))

    return sorted(scores, key=lambda x: -x[1])

def afficher_prediction(df, jeu):
    if jeu == "euro":
        colonnes_n = [f'N{i}' for i in range(1, 6)]
        colonnes_spe = [f'E{i}' for i in range(1, 3)]
        max_n, max_spe = 50, 12
    else:
        colonnes_n = [f'N{i}' for i in range(1, 6)]
        colonnes_spe = ["Chance"]
        max_n, max_spe = 49, 10

    st.markdown("### Réglage des pondérations")
    alpha = st.slider("Fréquence globale (α)", 0.0, 1.0, 0.4, 0.05)
    beta = st.slider("Fréquence récente (β)", 0.0, 1.0, 0.4, 0.05)
    gamma = st.slider("Corrélations (γ)", 0.0, 1.0, 0.2, 0.05)
    total = alpha + beta + gamma
    if total != 1.0:
        alpha /= total
        beta /= total
        gamma /= total

    recent_n = st.slider("Nombre de tirages récents à analyser", 20, 500, 100, 10)

    st.subheader("🔢 Prédiction des numéros")
    scores = score_predictif(df, colonnes_n, max_n, recent_n, alpha, beta, gamma)
    pred_n = [num for num, s in scores[:5]]
    st.success(f"Numéros à jouer : {pred_n}")
    df_scores_n = pd.DataFrame(scores, columns=["Numéro", "Score"]).set_index("Numéro")
    st.bar_chart(df_scores_n)

    st.subheader("⭐ Prédiction des étoiles / numéro Chance")
    scores_spe = score_predictif(df, colonnes_spe, max_spe, recent_n, alpha, beta, gamma)
    nb_spe = 2 if jeu == "euro" else 1
    pred_spe = [num for num, s in scores_spe[:nb_spe]]
    st.success(f"{'Étoiles' if jeu == 'euro' else 'Numéro Chance'} à jouer : {pred_spe}")
    df_scores_spe = pd.DataFrame(scores_spe, columns=["Numéro", "Score"]).set_index("Numéro")
    st.bar_chart(df_scores_spe)

    # Export CSV
    st.download_button("📤 Télécharger scores des numéros", df_scores_n.to_csv().encode(), "scores_numeros.csv", "text/csv")
    st.download_button("📤 Télécharger scores étoiles/Chance", df_scores_spe.to_csv().encode(), "scores_special.csv", "text/csv")

with tab1:
    st.header("🎯 Analyse EuroMillions")
    euro_file = st.file_uploader("📤 Charger le fichier CSV EuroMillions", type="csv", key="euro")
    if euro_file:
        df_euro = pd.read_csv(euro_file)
        afficher_prediction(df_euro, jeu="euro")

with tab2:
    st.header("🎯 Analyse Loto FDJ")
    loto_file = st.file_uploader("📤 Charger le fichier CSV Loto FDJ", type="csv", key="loto")
    if loto_file:
        df_loto = pd.read_csv(loto_file)
        afficher_prediction(df_loto, jeu="loto")
