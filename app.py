import os
import sys

# --- SÉCURITÉ ANTI-CRASH MAC (THREADING/TKINTER) ---
os.environ["TK_SILENCE_DEPRECATION"] = "1"
if sys.platform == "darwin":
    os.environ["MPLBACKEND"] = "Agg"

import streamlit as st
import psycopg2
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(page_title="ElitePro 37", layout="wide", page_icon="⚽")

# Configuration de la connexion PostgreSQL
DB_HOST = "elitepro37-db.postgres.database.azure.com"
DB_NAME = "postgres"  
DB_USER = "postgres"
DB_PASSWORD = "FootAzure2026!"  # Remplace par ton vrai mot de passe
DB_PORT = "5432"

def execution_query(query, params=None, fetch=True):
    """Fonction générique pour interroger PostgreSQL."""
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
        cursor = conn.cursor()
        cursor.execute(query, params)
        data = cursor.fetchall() if fetch else None
        if not fetch:
            conn.commit()
        cursor.close()
        conn.close()
        return data
    except Exception as e:
        st.error(f"Erreur de connexion BDD : {e}")
        return []

# --- HYPER-FORCE MODE SOMBRE (CSS FONCE GLOBAL) ---
st.markdown("""
    <style>
    /* Forcer l'application entière, le fond et la sidebar en sombre */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }
    [data-testid="stSidebar"] {
        background-color: #161920 !important;
    }
    
    /* Forcer absolument TOUS les textes et paragraphes en blanc/gris clair */
    h1, h2, h3, h4, h5, h6, p, label, span, li, div {
        color: #fafafa !important;
    }
    
    /* Configurer les boutons classiques pour qu'ils soient gris foncé avec écriture blanche */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #262730 !important;
        color: #ffffff !important;
        border: 1px solid #4a4b50 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }
    .stButton>button:hover { 
        background-color: #ff4b4b !important; 
        color: white !important; 
        border-color: #ff4b4b !important; 
    }
    
    /* Le bloc de score */
    .score-box {
        background: linear-gradient(135deg, #262730 0%, #111111 100%);
        padding: 8px 15px;
        border-radius: 8px;
        text-align: center;
        font-weight: 800;
        font-size: 22px;
        color: #ff4b4b !important;
        border: 1px solid #374151;
    }
    .logo-container { display: flex; justify-content: center; align-items: center; height: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'selected_team' not in st.session_state:
    st.session_state.selected_team = None

# --- PAGE ACCUEIL ---
if st.session_state.page == 'home':
    st.title("⚽ ElitePro 37")
    
    # --- SIDEBAR CONFIGURATION ---
    st.sidebar.header("Configuration")
    league_name = st.sidebar.selectbox("Choisir une Ligue", ["Champions League", "Premier League", "Ligue 1"])
    codes = {"Champions League": "CL", "Premier League": "PL", "Ligue 1": "FL1"}
    league_code = codes[league_name]
    
    filtre = st.sidebar.radio("Statut des matchs", ["Matchs terminés", "Matchs à venir"])
    db_status = "FINISHED" if filtre == "Matchs terminés" else "TIMED"
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Chercher une équipe")
    search_query = st.sidebar.text_input("Nom de l'équipe", placeholder="Ex: Bayern...")

    # --- SÉLECTEUR DE CLASSEMENT DYNAMIQUE (POSTGRESQL) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏆 Top 5 Classement")
    
    query_classement = """
        WITH points_calcul AS (
            SELECT equipe_dom_id AS eq_id, CASE WHEN score_dom > score_ext THEN 3 WHEN score_dom = score_ext THEN 1 ELSE 0 END AS pts FROM matchs_locaux WHERE league_code = %s AND statut = 'FINISHED'
            UNION ALL
            SELECT equipe_ext_id AS eq_id, CASE WHEN score_ext > score_dom THEN 3 WHEN score_dom = score_ext THEN 1 ELSE 0 END AS pts FROM matchs_locaux WHERE league_code = %s AND statut = 'FINISHED'
        )
        SELECT e.nom, SUM(p.pts) as total_pts 
        FROM points_calcul p 
        JOIN equipes_locales e ON p.eq_id = e.id 
        GROUP BY e.nom ORDER BY total_pts DESC LIMIT 5;
    """
    top_teams = execution_query(query_classement, (league_code, league_code))
    
    if top_teams:
        for idx, team in enumerate(top_teams, 1):
            st.sidebar.write(f"{idx}. {team[0]} - **{team[1]} pts**")
    else:
        st.sidebar.write("Aucun match terminé pour cette ligue.")

    # --- LOGIQUE RECHERCHE ÉQUIPE ---
    if search_query:
        query_search = "SELECT id, nom FROM equipes_locales WHERE nom ILIKE %s;"
        search_results = execution_query(query_search, (f"%{search_query}%",))
        if search_results:
            for tid, name in search_results:
                if st.sidebar.button(f"👉 Voir {name}", key=f"search_{tid}"):
                    st.session_state.selected_team = tid
                    st.session_state.page = 'team_details'
                    st.rerun()

    # --- AFFICHAGE DES MATCHS DEPUIS POSTGRESQL ---
    query_matchs = """
        SELECT m.id, ed.nom, ed.crest_url, ee.nom, ee.crest_url, m.score_dom, m.score_ext, m.statut, m.date_match, ed.id, ee.id
        FROM matchs_locaux m
        JOIN equipes_locales ed ON m.equipe_dom_id = ed.id
        JOIN equipes_locales ee ON m.equipe_ext_id = ee.id
        WHERE m.league_code = %s AND m.statut = %s
        ORDER BY m.date_match DESC;
    """
    match_list = execution_query(query_matchs, (league_code, db_status))
    
    if match_list:
        for match in match_list[:10]:
            mid, h_nom, h_crest, a_nom, a_crest, s_dom, s_ext, status, d_match, hid, aid = match
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 1, 3])
                
                # Bouton Équipe Domicile classique (Gris foncé, texte blanc forcé)
                with col1:
                    if st.button(h_nom, key=f"h_{mid}"):
                        st.session_state.selected_team = hid; st.session_state.page = 'team_details'; st.rerun()
                        
                with col2:
                    st.markdown(f'<div class="logo-container"><img src="{h_crest}" width="40"></div>', unsafe_allow_html=True)
                
                with col3:
                    score_text = f"{s_dom} - {s_ext}" if status == "FINISHED" else str(d_match)[11:16]
                    st.markdown(f"<div class='score-box'>{score_text}</div>", unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f'<div class="logo-container"><img src="{a_crest}" width="40"></div>', unsafe_allow_html=True)
                
                # Bouton Équipe Extérieur classique (Gris foncé, texte blanc forcé)
                with col5:
                    if st.button(a_nom, key=f"a_{mid}"):
                        st.session_state.selected_team = aid; st.session_state.page = 'team_details'; st.rerun()
                        
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("Aucun match trouvé pour ces critères dans la base de données locale.")

# --- PAGE DÉTAILS ÉQUIPE VIA POSTGRES ---
elif st.session_state.page == 'team_details':
    if st.button("⬅️ Retour"):
        st.session_state.page = 'home'; st.rerun()
        
    team_id = st.session_state.selected_team
    team_data = execution_query("SELECT nom, crest_url FROM equipes_locales WHERE id = %s;", (team_id,))
    
    if team_data:
        nom_equipe, crest_url = team_data[0]
        st.divider()
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f'<img src="{crest_url}" width="150">', unsafe_allow_html=True)
        with c2:
            st.title(nom_equipe)
            st.info(f"📊 Données extraites de PostgreSQL pour l'ID équipe : {team_id}")
        
        st.subheader("📊 Statistiques de performance simulées")
        labels = ['Attaque', 'Défense', 'Milieu', 'Vitesse', 'Mental']
        values = [85, 78, 82, 80, 89] 
        fig = go.Figure([go.Bar(x=labels, y=values, marker_color='#ff4b4b')])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
        st.plotly_chart(fig, use_container_width=True)