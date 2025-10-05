"""
Module de gestion des fournisseurs et sous-traitants
Base de données pour stocker et récupérer les informations automatiquement
"""

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime
import pandas as pd

def init_fournisseurs_db():
    """Initialise la base de données des fournisseurs"""
    # Utiliser le même répertoire que les autres bases de données
    data_dir = os.getenv('DATA_DIR', 'data')
    db_path = os.path.join(data_dir, 'fournisseurs.db')
    os.makedirs(data_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table principale des fournisseurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fournisseurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE NOT NULL,
            type TEXT DEFAULT 'Fournisseur',
            contact_principal TEXT,
            telephone TEXT,
            cellulaire TEXT,
            email TEXT,
            adresse TEXT,
            ville TEXT,
            province TEXT DEFAULT 'Québec',
            code_postal TEXT,
            site_web TEXT,
            numero_entreprise TEXT,
            tps TEXT,
            tvq TEXT,
            rbq TEXT,
            specialites TEXT,
            conditions_paiement TEXT DEFAULT 'Net 30 jours',
            delai_livraison TEXT,
            notes TEXT,
            actif INTEGER DEFAULT 1,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            derniere_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table pour l'historique des prix (pour référence future)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historique_prix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fournisseur_id INTEGER,
            description TEXT,
            prix_unitaire REAL,
            unite TEXT,
            date_prix DATE,
            projet_reference TEXT,
            notes TEXT,
            FOREIGN KEY (fournisseur_id) REFERENCES fournisseurs(id)
        )
    ''')

    # Index pour optimiser les recherches
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fournisseur_nom ON fournisseurs(nom)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fournisseur_type ON fournisseurs(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fournisseur_actif ON fournisseurs(actif)')

    conn.commit()

    # Ajouter quelques fournisseurs de démonstration si la table est vide
    cursor.execute('SELECT COUNT(*) FROM fournisseurs')
    if cursor.fetchone()[0] == 0:
        insert_demo_fournisseurs(cursor)
        conn.commit()

    conn.close()

def insert_demo_fournisseurs(cursor):
    """Insère des fournisseurs de démonstration"""
    demo_fournisseurs = [
        {
            'nom': 'Matériaux ABC Inc.',
            'type': 'Fournisseur',
            'contact_principal': 'Jean Tremblay',
            'telephone': '514-555-1234',
            'cellulaire': '514-555-5678',
            'email': 'info@materiauxabc.ca',
            'adresse': '1234 Rue Industrielle',
            'ville': 'Montréal',
            'province': 'Québec',
            'code_postal': 'H1A 2B3',
            'site_web': 'www.materiauxabc.ca',
            'numero_entreprise': '1234567890',
            'tps': '123456789RT0001',
            'tvq': '1234567890TQ0001',
            'specialites': 'Bois, Quincaillerie, Matériaux de construction',
            'conditions_paiement': 'Net 30 jours',
            'delai_livraison': '24-48 heures'
        },
        {
            'nom': 'Électricité Pro',
            'type': 'Sous-traitant',
            'contact_principal': 'Marie Dubois',
            'telephone': '514-555-9876',
            'cellulaire': '514-555-4321',
            'email': 'contact@electricitepro.ca',
            'adresse': '5678 Boulevard Commercial',
            'ville': 'Laval',
            'province': 'Québec',
            'code_postal': 'H7N 4K5',
            'rbq': '5678-9012-34',
            'specialites': 'Installation électrique, Panneaux, Éclairage',
            'conditions_paiement': 'Net 15 jours',
            'delai_livraison': 'Selon disponibilité'
        },
        {
            'nom': 'Plomberie Moderne',
            'type': 'Sous-traitant',
            'contact_principal': 'Pierre Gagnon',
            'telephone': '450-555-3456',
            'email': 'info@plomberiemoderne.ca',
            'adresse': '9012 Rue des Artisans',
            'ville': 'Brossard',
            'province': 'Québec',
            'code_postal': 'J4W 3H7',
            'rbq': '9876-5432-10',
            'specialites': 'Plomberie, Chauffage, Ventilation',
            'conditions_paiement': 'Net 30 jours'
        }
    ]

    for fournisseur in demo_fournisseurs:
        placeholders = ', '.join(['?' for _ in fournisseur])
        columns = ', '.join(fournisseur.keys())
        query = f'INSERT OR IGNORE INTO fournisseurs ({columns}) VALUES ({placeholders})'
        cursor.execute(query, list(fournisseur.values()))

def get_fournisseurs_list(actif_seulement=True):
    """Récupère la liste des fournisseurs"""
    data_dir = os.getenv('DATA_DIR', 'data')
    db_path = os.path.join(data_dir, 'fournisseurs.db')

    if not os.path.exists(db_path):
        init_fournisseurs_db()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if actif_seulement:
        cursor.execute('SELECT nom FROM fournisseurs WHERE actif = 1 ORDER BY nom')
    else:
        cursor.execute('SELECT nom FROM fournisseurs ORDER BY nom')

    fournisseurs = [row[0] for row in cursor.fetchall()]
    conn.close()

    return fournisseurs

def get_fournisseur_by_nom(nom):
    """Récupère les informations d'un fournisseur par son nom"""
    data_dir = os.getenv('DATA_DIR', 'data')
    db_path = os.path.join(data_dir, 'fournisseurs.db')

    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM fournisseurs WHERE nom = ?', (nom,))
    row = cursor.fetchone()

    if row:
        columns = [description[0] for description in cursor.description]
        fournisseur = dict(zip(columns, row))
    else:
        fournisseur = None

    conn.close()
    return fournisseur

def save_fournisseur(fournisseur_data):
    """Sauvegarde ou met à jour un fournisseur"""
    data_dir = os.getenv('DATA_DIR', 'data')
    db_path = os.path.join(data_dir, 'fournisseurs.db')

    if not os.path.exists(db_path):
        init_fournisseurs_db()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Vérifier si le fournisseur existe déjà
    cursor.execute('SELECT id FROM fournisseurs WHERE nom = ?', (fournisseur_data['nom'],))
    existing = cursor.fetchone()

    if existing:
        # Mise à jour
        fournisseur_data['derniere_modification'] = datetime.now().isoformat()
        update_fields = [f"{key} = ?" for key in fournisseur_data.keys() if key != 'id']
        update_query = f"UPDATE fournisseurs SET {', '.join(update_fields)} WHERE id = ?"
        values = list(fournisseur_data.values()) + [existing[0]]
        cursor.execute(update_query, values)
    else:
        # Insertion
        columns = ', '.join(fournisseur_data.keys())
        placeholders = ', '.join(['?' for _ in fournisseur_data])
        insert_query = f"INSERT INTO fournisseurs ({columns}) VALUES ({placeholders})"
        cursor.execute(insert_query, list(fournisseur_data.values()))

    conn.commit()
    conn.close()

    return True

def delete_fournisseur(nom):
    """Supprime un fournisseur (le marque comme inactif)"""
    data_dir = os.getenv('DATA_DIR', 'data')
    db_path = os.path.join(data_dir, 'fournisseurs.db')

    if not os.path.exists(db_path):
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # On ne supprime pas vraiment, on marque comme inactif
    cursor.execute('UPDATE fournisseurs SET actif = 0 WHERE nom = ?', (nom,))

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    return success

def show_fournisseurs_interface():
    """Interface Streamlit pour gérer les fournisseurs"""
    st.subheader("🏢 Gestion des Fournisseurs")

    # Initialiser la base de données
    init_fournisseurs_db()

    # Tabs pour les différentes actions
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Liste", "➕ Ajouter", "✏️ Modifier", "📊 Statistiques"])

    with tab1:
        st.markdown("### Liste des Fournisseurs")

        # Options de filtrage
        col1, col2, col3 = st.columns(3)
        with col1:
            show_inactive = st.checkbox("Afficher les inactifs", False)
        with col2:
            filter_type = st.selectbox("Type", ["Tous", "Fournisseur", "Sous-traitant"])
        with col3:
            search_term = st.text_input("🔍 Rechercher")

        # Récupérer et afficher les fournisseurs
        data_dir = os.getenv('DATA_DIR', 'data')
        db_path = os.path.join(data_dir, 'fournisseurs.db')

        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)

            query = "SELECT * FROM fournisseurs WHERE 1=1"
            params = []

            if not show_inactive:
                query += " AND actif = 1"

            if filter_type != "Tous":
                query += " AND type = ?"
                params.append(filter_type)

            if search_term:
                query += " AND (nom LIKE ? OR specialites LIKE ? OR contact_principal LIKE ?)"
                params.extend([f"%{search_term}%"] * 3)

            query += " ORDER BY nom"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if not df.empty:
                # Affichage sous forme de cartes
                for idx, row in df.iterrows():
                    with st.expander(f"**{row.get('nom', 'Sans nom')}** - {row.get('type', 'Fournisseur')}", expanded=False):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**Informations de contact:**")
                            if row.get('contact_principal'):
                                st.write(f"👤 {row.get('contact_principal')}")
                            if row.get('telephone'):
                                st.write(f"📞 {row.get('telephone')}")
                            if row.get('cellulaire'):
                                st.write(f"📱 {row.get('cellulaire')}")
                            if row.get('email'):
                                st.write(f"✉️ {row.get('email')}")
                            if row.get('site_web'):
                                st.write(f"🌐 {row.get('site_web')}")

                        with col2:
                            st.markdown("**Adresse:**")
                            if row.get('adresse'):
                                st.write(row.get('adresse'))
                            if row.get('ville'):
                                st.write(f"{row.get('ville')}, {row.get('province', 'Québec')} {row.get('code_postal', '')}")

                            if row.get('rbq'):
                                st.write(f"**RBQ:** {row.get('rbq')}")
                            if row.get('specialites'):
                                st.write(f"**Spécialités:** {row.get('specialites')}")

                        if row.get('notes'):
                            st.markdown("**Notes:**")
                            st.info(row.get('notes'))

                        # Actions
                        col1, col2, col3 = st.columns([1, 1, 4])
                        with col1:
                            if st.button(f"✏️ Modifier", key=f"edit_fournisseur_{idx}_{row.get('nom', '')}"):
                                st.session_state.edit_fournisseur = row.get('nom')
                                st.rerun()

                        with col2:
                            if row.get('actif', True):
                                if st.button(f"🗑️ Désactiver", key=f"delete_fournisseur_{idx}_{row.get('nom', '')}"):
                                    delete_fournisseur(row.get('nom'))
                                    st.success(f"{row.get('nom')} a été désactivé")
                                    st.rerun()
                            else:
                                if st.button(f"✅ Réactiver", key=f"activate_fournisseur_{idx}_{row.get('nom', '')}"):
                                    conn = sqlite3.connect(db_path)
                                    cursor = conn.cursor()
                                    cursor.execute('UPDATE fournisseurs SET actif = 1 WHERE nom = ?', (row.get('nom'),))
                                    conn.commit()
                                    conn.close()
                                    st.success(f"{row.get('nom')} a été réactivé")
                                    st.rerun()
            else:
                st.info("Aucun fournisseur trouvé")

    with tab2:
        st.markdown("### Ajouter un Nouveau Fournisseur")

        with st.form("add_fournisseur"):
            col1, col2 = st.columns(2)

            with col1:
                nom = st.text_input("Nom de l'entreprise *", help="Nom unique du fournisseur")
                type_fournisseur = st.selectbox("Type", ["Fournisseur", "Sous-traitant"])
                contact_principal = st.text_input("Contact principal")
                telephone = st.text_input("Téléphone")
                cellulaire = st.text_input("Cellulaire")
                email = st.text_input("Email")

            with col2:
                adresse = st.text_input("Adresse")
                ville = st.text_input("Ville")
                province = st.text_input("Province", value="Québec")
                code_postal = st.text_input("Code postal")
                site_web = st.text_input("Site web")
                rbq = st.text_input("Numéro RBQ")

            specialites = st.text_area("Spécialités", help="Services offerts, produits disponibles")
            conditions_paiement = st.text_input("Conditions de paiement", value="Net 30 jours")
            delai_livraison = st.text_input("Délai de livraison habituel")
            notes = st.text_area("Notes")

            if st.form_submit_button("💾 Enregistrer", type="primary"):
                if nom:
                    fournisseur_data = {
                        'nom': nom,
                        'type': type_fournisseur,
                        'contact_principal': contact_principal,
                        'telephone': telephone,
                        'cellulaire': cellulaire,
                        'email': email,
                        'adresse': adresse,
                        'ville': ville,
                        'province': province,
                        'code_postal': code_postal,
                        'site_web': site_web,
                        'rbq': rbq,
                        'specialites': specialites,
                        'conditions_paiement': conditions_paiement,
                        'delai_livraison': delai_livraison,
                        'notes': notes
                    }

                    if save_fournisseur(fournisseur_data):
                        st.success(f"✅ {nom} a été ajouté avec succès!")
                        st.balloons()
                    else:
                        st.error("Erreur lors de l'ajout du fournisseur")
                else:
                    st.error("Le nom du fournisseur est obligatoire")

    with tab3:
        st.markdown("### Modifier un Fournisseur")

        # Sélection du fournisseur à modifier
        fournisseur_a_modifier = st.selectbox(
            "Sélectionner un fournisseur",
            [""] + get_fournisseurs_list(actif_seulement=False)
        )

        if fournisseur_a_modifier:
            fournisseur = get_fournisseur_by_nom(fournisseur_a_modifier)

            if fournisseur:
                with st.form("edit_fournisseur"):
                    col1, col2 = st.columns(2)

                    with col1:
                        nom = st.text_input("Nom de l'entreprise *", value=fournisseur['nom'], disabled=True)
                        type_fournisseur = st.selectbox("Type", ["Fournisseur", "Sous-traitant"],
                                                       index=0 if fournisseur['type'] == "Fournisseur" else 1)
                        contact_principal = st.text_input("Contact principal", value=fournisseur['contact_principal'] or "")
                        telephone = st.text_input("Téléphone", value=fournisseur['telephone'] or "")
                        cellulaire = st.text_input("Cellulaire", value=fournisseur['cellulaire'] or "")
                        email = st.text_input("Email", value=fournisseur['email'] or "")

                    with col2:
                        adresse = st.text_input("Adresse", value=fournisseur['adresse'] or "")
                        ville = st.text_input("Ville", value=fournisseur['ville'] or "")
                        province = st.text_input("Province", value=fournisseur['province'] or "Québec")
                        code_postal = st.text_input("Code postal", value=fournisseur['code_postal'] or "")
                        site_web = st.text_input("Site web", value=fournisseur['site_web'] or "")
                        rbq = st.text_input("Numéro RBQ", value=fournisseur['rbq'] or "")

                    specialites = st.text_area("Spécialités", value=fournisseur['specialites'] or "")
                    conditions_paiement = st.text_input("Conditions de paiement", value=fournisseur['conditions_paiement'] or "Net 30 jours")
                    delai_livraison = st.text_input("Délai de livraison habituel", value=fournisseur['delai_livraison'] or "")
                    notes = st.text_area("Notes", value=fournisseur['notes'] or "")

                    if st.form_submit_button("💾 Mettre à jour", type="primary"):
                        fournisseur_data = {
                            'nom': nom,
                            'type': type_fournisseur,
                            'contact_principal': contact_principal,
                            'telephone': telephone,
                            'cellulaire': cellulaire,
                            'email': email,
                            'adresse': adresse,
                            'ville': ville,
                            'province': province,
                            'code_postal': code_postal,
                            'site_web': site_web,
                            'rbq': rbq,
                            'specialites': specialites,
                            'conditions_paiement': conditions_paiement,
                            'delai_livraison': delai_livraison,
                            'notes': notes
                        }

                        if save_fournisseur(fournisseur_data):
                            st.success(f"✅ {nom} a été mis à jour avec succès!")
                        else:
                            st.error("Erreur lors de la mise à jour")

    with tab4:
        st.markdown("### 📊 Statistiques")

        data_dir = os.getenv('DATA_DIR', 'data')
        db_path = os.path.join(data_dir, 'fournisseurs.db')

        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)

            # Statistiques générales
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM fournisseurs WHERE actif = 1')
                count_active = cursor.fetchone()[0]
                st.metric("Fournisseurs actifs", count_active)

            with col2:
                cursor.execute('SELECT COUNT(*) FROM fournisseurs WHERE type = "Fournisseur" AND actif = 1')
                count_fournisseurs = cursor.fetchone()[0]
                st.metric("Fournisseurs", count_fournisseurs)

            with col3:
                cursor.execute('SELECT COUNT(*) FROM fournisseurs WHERE type = "Sous-traitant" AND actif = 1')
                count_soustraitants = cursor.fetchone()[0]
                st.metric("Sous-traitants", count_soustraitants)

            with col4:
                cursor.execute('SELECT COUNT(*) FROM fournisseurs WHERE actif = 0')
                count_inactive = cursor.fetchone()[0]
                st.metric("Inactifs", count_inactive)

            # Graphiques
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                # Répartition par type
                st.markdown("**Répartition par type**")
                df_type = pd.read_sql_query(
                    'SELECT type, COUNT(*) as count FROM fournisseurs WHERE actif = 1 GROUP BY type',
                    conn
                )
                if not df_type.empty:
                    st.bar_chart(df_type.set_index('type'))

            with col2:
                # Répartition par ville
                st.markdown("**Répartition géographique**")
                df_ville = pd.read_sql_query(
                    'SELECT ville, COUNT(*) as count FROM fournisseurs WHERE actif = 1 AND ville IS NOT NULL GROUP BY ville ORDER BY count DESC LIMIT 10',
                    conn
                )
                if not df_ville.empty:
                    st.bar_chart(df_ville.set_index('ville'))

            conn.close()
