import psycopg2
import requests

# 1. Configuration de la connexion (Mets ton vrai mot de passe Postgres ici)
DB_HOST = "elitepro37-db.postgres.database.azure.com"
DB_NAME = "postgres"  # Par défaut Azure crée une base nommée postgres
DB_USER = "postgres"
DB_PASSWORD = "FootAzure2026!"  # Remplace par ton vrai mot de passe
DB_PORT = "5432"

def initialiser_projet():
    try:
        # Connexion à PostgreSQL
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
        cursor = conn.cursor()
        
        print("⚡ Connexion à PostgreSQL réussie. Création des tables...")

        # Suppression des anciennes tables si elles existent pour repartir à zéro
        cursor.execute("DROP TABLE IF EXISTS matchs_locaux CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS equipes_locales CASCADE;")

        # Création de la table Équipes
        cursor.execute('''
            CREATE TABLE equipes_locales (
                id INTEGER PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                crest_url TEXT
            );
        ''')
        
        # Création de la table Matchs
        cursor.execute('''
            CREATE TABLE matchs_locaux (
                id SERIAL PRIMARY KEY,
                league_code VARCHAR(10) NOT NULL,
                equipe_dom_id INTEGER REFERENCES equipes_locales(id) ON DELETE CASCADE,
                equipe_ext_id INTEGER REFERENCES equipes_locales(id) ON DELETE CASCADE,
                score_dom INTEGER DEFAULT 0,
                score_ext INTEGER DEFAULT 0,
                statut VARCHAR(50) NOT NULL,
                date_match TIMESTAMP
            );
        ''')
        conn.commit()
        print("✅ Tables créées avec succès !")

        # 2. Remplissage de la base avec les vraies données de l'API (CL, PL, FL1)
        API_KEY = "22827ef19b104c63afd8b28fd9e19bc6"
        headers = {'X-Auth-Token': API_KEY}
        ligues = ["CL", "PL", "FL1"]

        print("📥 Récupération des données depuis l'API football-data...")
        
        for ligue in ligues:
            url = f"https://api.football-data.org/v4/competitions/{ligue}/matches"
            res = requests.get(url, headers=headers)
            
            if res.status_code == 200:
                data = res.json()
                matchs_ajoutes = 0
                
                for m in data.get('matches', [])[:30]:  # On prend les 30 premiers matchs de chaque ligue
                    # Insertion Équipe Domicile
                    cursor.execute("""
                        INSERT INTO equipes_locales (id, nom, crest_url) 
                        VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING;
                    """, (m['homeTeam']['id'], m['homeTeam']['shortName'], m['homeTeam']['crest']))
                    
                    # Insertion Équipe Extérieur
                    cursor.execute("""
                        INSERT INTO equipes_locales (id, nom, crest_url) 
                        VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING;
                    """, (m['awayTeam']['id'], m['awayTeam']['shortName'], m['awayTeam']['crest']))
                    
                    # Extraction des scores (gestion des None pour les matchs à venir)
                    s_dom = m['score']['fullTime']['home'] if m['score']['fullTime']['home'] is not None else 0
                    s_ext = m['score']['fullTime']['away'] if m['score']['fullTime']['away'] is not None else 0
                    
                    # Insertion du Match
                    cursor.execute("""
                        INSERT INTO matchs_locaux (league_code, equipe_dom_id, equipe_ext_id, score_dom, score_ext, statut, date_match) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (ligue, m['homeTeam']['id'], m['awayTeam']['id'], s_dom, s_ext, m['status'], m['utcDate']))
                    
                    matchs_ajoutes += 1
                
                conn.commit()
                print(f"⚽ {matchs_ajoutes} matchs chargés pour la ligue {ligue}.")
            else:
                print(f"❌ Impossible de récupérer la ligue {ligue} (Code: {res.status_code})")

        cursor.close()
        conn.close()
        print("\n🔥 BASE DE DONNÉES PRÊTE ET REMPLIE ! Tu peux lancer l'application.")

    except Exception as e:
        print(f"❌ Erreur critique : {e}")

if __name__ == "__main__":
    initialiser_projet()