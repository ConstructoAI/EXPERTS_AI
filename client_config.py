"""
Module de gestion de la configuration des clients pour EXPERTS IA
Permet la sauvegarde et la réutilisation des informations clients dans les soumissions
"""

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime

# Base de données pour les clients
DB_PATH = 'clients.db'


def init_clients_table():
    """Initialise la table des clients"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            adresse TEXT,
            ville TEXT,
            province TEXT DEFAULT 'Québec',
            code_postal TEXT,
            telephone_bureau TEXT,
            telephone_cellulaire TEXT,
            email TEXT,
            contact_principal_nom TEXT,
            contact_principal_titre TEXT,
            contact_principal_telephone TEXT,
            contact_principal_email TEXT,
            notes TEXT,
            date_creation TEXT,
            date_modification TEXT,
            actif INTEGER DEFAULT 1
        )
    ''')

    conn.commit()

    # Vérifier si on a des clients
    cursor.execute('SELECT COUNT(*) FROM clients')
    count = cursor.fetchone()[0]

    # Si aucun client, créer un client par défaut
    if count == 0:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO clients (
                nom, adresse, ville, province, code_postal,
                telephone_bureau, telephone_cellulaire, email,
                contact_principal_nom, contact_principal_titre,
                contact_principal_telephone, contact_principal_email,
                notes, date_creation, date_modification, actif
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Construction Résidentielle Laval Inc.',
            '450 Boulevard des Laurentides',
            'Laval',
            'Québec',
            'H7G 2V1',
            '450-555-1234',
            '514-555-5678',
            'info@constructionlaval.ca',
            'Jean-Pierre Tremblay',
            'Directeur de projets',
            '514-555-5678',
            'jp.tremblay@constructionlaval.ca',
            'Client exemple créé par défaut. Projet résidentiel typique avec bonnes références.',
            now,
            now,
            1
        ))
        conn.commit()
        print("[CLIENT DB] Client par défaut créé: Construction Résidentielle Laval Inc.")

    conn.close()


def get_all_clients(actif_seulement=True):
    """Récupère tous les clients"""
    init_clients_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if actif_seulement:
        cursor.execute('SELECT * FROM clients WHERE actif = 1 ORDER BY nom')
    else:
        cursor.execute('SELECT * FROM clients ORDER BY nom')

    colonnes = [description[0] for description in cursor.description]
    clients = []

    for row in cursor.fetchall():
        client = dict(zip(colonnes, row))
        clients.append(client)

    conn.close()
    return clients


def get_client_by_id(client_id):
    """Récupère un client par son ID"""
    init_clients_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
    colonnes = [description[0] for description in cursor.description]
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(zip(colonnes, row))
    return None


def save_client(client_data, client_id=None):
    """Sauvegarde ou met à jour un client"""
    init_clients_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if client_id:
        # Mise à jour
        cursor.execute('''
            UPDATE clients SET
                nom = ?,
                adresse = ?,
                ville = ?,
                province = ?,
                code_postal = ?,
                telephone_bureau = ?,
                telephone_cellulaire = ?,
                email = ?,
                contact_principal_nom = ?,
                contact_principal_titre = ?,
                contact_principal_telephone = ?,
                contact_principal_email = ?,
                notes = ?,
                date_modification = ?
            WHERE id = ?
        ''', (
            client_data.get('nom', ''),
            client_data.get('adresse', ''),
            client_data.get('ville', ''),
            client_data.get('province', 'Québec'),
            client_data.get('code_postal', ''),
            client_data.get('telephone_bureau', ''),
            client_data.get('telephone_cellulaire', ''),
            client_data.get('email', ''),
            client_data.get('contact_principal_nom', ''),
            client_data.get('contact_principal_titre', ''),
            client_data.get('contact_principal_telephone', ''),
            client_data.get('contact_principal_email', ''),
            client_data.get('notes', ''),
            now,
            client_id
        ))
    else:
        # Insertion
        cursor.execute('''
            INSERT INTO clients (
                nom, adresse, ville, province, code_postal,
                telephone_bureau, telephone_cellulaire, email,
                contact_principal_nom, contact_principal_titre,
                contact_principal_telephone, contact_principal_email,
                notes, date_creation, date_modification, actif
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_data.get('nom', ''),
            client_data.get('adresse', ''),
            client_data.get('ville', ''),
            client_data.get('province', 'Québec'),
            client_data.get('code_postal', ''),
            client_data.get('telephone_bureau', ''),
            client_data.get('telephone_cellulaire', ''),
            client_data.get('email', ''),
            client_data.get('contact_principal_nom', ''),
            client_data.get('contact_principal_titre', ''),
            client_data.get('contact_principal_telephone', ''),
            client_data.get('contact_principal_email', ''),
            client_data.get('notes', ''),
            now,
            now,
            1
        ))
        client_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return client_id


def delete_client(client_id):
    """Désactive un client (soft delete)"""
    init_clients_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('UPDATE clients SET actif = 0 WHERE id = ?', (client_id,))

    conn.commit()
    conn.close()


def show_clients_management():
    """Interface Streamlit pour gérer les clients"""

    st.markdown("## 👥 Gestion des Clients")

    # Message si modification en cours
    if 'client_a_modifier' in st.session_state and st.session_state.client_a_modifier:
        client_temp = get_client_by_id(st.session_state.client_a_modifier)
        if client_temp:
            st.info(f"✏️ **Mode modification activé** pour le client: **{client_temp['nom']}**. Allez dans l'onglet '➕ Ajouter/Modifier' pour modifier les informations.")

    # Onglets
    tab1, tab2 = st.tabs(["📋 Liste des clients", "➕ Ajouter/Modifier"])

    with tab1:
        st.markdown("### Liste des clients")

        clients = get_all_clients()

        if not clients:
            st.info("Aucun client enregistré. Utilisez l'onglet 'Ajouter/Modifier' pour créer un nouveau client.")
        else:
            # Afficher les clients sous forme de cartes
            for client in clients:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"**{client['nom']}**")
                        if client['adresse']:
                            st.caption(f"📍 {client['adresse']}, {client['ville']} {client['code_postal']}")
                        if client['email']:
                            st.caption(f"📧 {client['email']}")
                        if client['telephone_bureau']:
                            st.caption(f"📞 {client['telephone_bureau']}")

                    with col2:
                        if st.button("✏️ Modifier", key=f"edit_{client['id']}"):
                            st.session_state.client_a_modifier = client['id']
                            st.rerun()

                    with col3:
                        if st.button("🗑️ Supprimer", key=f"delete_{client['id']}"):
                            if st.session_state.get(f'confirm_delete_{client["id"]}'):
                                delete_client(client['id'])
                                st.success(f"Client {client['nom']} supprimé")
                                st.rerun()
                            else:
                                st.session_state[f'confirm_delete_{client["id"]}'] = True
                                st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression")

                    st.divider()

    with tab2:
        # Vérifier si on modifie un client existant
        client_a_modifier = None
        if 'client_a_modifier' in st.session_state:
            client_a_modifier = get_client_by_id(st.session_state.client_a_modifier)
            if client_a_modifier:
                st.markdown(f"### ✏️ Modification : {client_a_modifier['nom']}")
            else:
                st.session_state.pop('client_a_modifier', None)
        else:
            st.markdown("### ➕ Nouveau Client")

        with st.form("form_client"):
            st.markdown("#### Informations générales")

            col1, col2 = st.columns(2)

            with col1:
                nom = st.text_input(
                    "Nom du client *",
                    value=client_a_modifier['nom'] if client_a_modifier else "",
                    help="Nom complet du client (entreprise ou particulier)"
                )

                adresse = st.text_input(
                    "Adresse",
                    value=client_a_modifier['adresse'] if client_a_modifier else ""
                )

                ville = st.text_input(
                    "Ville",
                    value=client_a_modifier['ville'] if client_a_modifier else ""
                )

            with col2:
                province = st.selectbox(
                    "Province",
                    options=['Québec', 'Ontario', 'Nouveau-Brunswick', 'Nouvelle-Écosse', 'Autre'],
                    index=0 if not client_a_modifier else (['Québec', 'Ontario', 'Nouveau-Brunswick', 'Nouvelle-Écosse', 'Autre'].index(client_a_modifier['province']) if client_a_modifier['province'] in ['Québec', 'Ontario', 'Nouveau-Brunswick', 'Nouvelle-Écosse', 'Autre'] else 0)
                )

                code_postal = st.text_input(
                    "Code postal",
                    value=client_a_modifier['code_postal'] if client_a_modifier else "",
                    max_chars=7
                )

            st.markdown("#### Coordonnées")

            col1, col2 = st.columns(2)

            with col1:
                telephone_bureau = st.text_input(
                    "Téléphone bureau",
                    value=client_a_modifier['telephone_bureau'] if client_a_modifier else "",
                    help="Format: 514-123-4567"
                )

                email = st.text_input(
                    "Courriel",
                    value=client_a_modifier['email'] if client_a_modifier else ""
                )

            with col2:
                telephone_cellulaire = st.text_input(
                    "Téléphone cellulaire",
                    value=client_a_modifier['telephone_cellulaire'] if client_a_modifier else ""
                )

            st.markdown("#### Personne contact")

            col1, col2 = st.columns(2)

            with col1:
                contact_nom = st.text_input(
                    "Nom du contact",
                    value=client_a_modifier['contact_principal_nom'] if client_a_modifier else ""
                )

                contact_titre = st.text_input(
                    "Titre / Fonction",
                    value=client_a_modifier['contact_principal_titre'] if client_a_modifier else "",
                    help="Ex: Directeur, Propriétaire, etc."
                )

            with col2:
                contact_telephone = st.text_input(
                    "Téléphone contact",
                    value=client_a_modifier['contact_principal_telephone'] if client_a_modifier else ""
                )

                contact_email = st.text_input(
                    "Courriel contact",
                    value=client_a_modifier['contact_principal_email'] if client_a_modifier else ""
                )

            st.markdown("#### Notes")
            notes = st.text_area(
                "Notes internes",
                value=client_a_modifier['notes'] if client_a_modifier else "",
                help="Informations additionnelles, préférences, historique, etc.",
                height=100
            )

            col1, col2 = st.columns([1, 4])

            with col1:
                submitted = st.form_submit_button(
                    "💾 Sauvegarder" if client_a_modifier else "➕ Créer",
                    use_container_width=True
                )

            with col2:
                if client_a_modifier:
                    if st.form_submit_button("❌ Annuler", use_container_width=True):
                        st.session_state.pop('client_a_modifier', None)
                        st.rerun()

            if submitted:
                if not nom:
                    st.error("⚠️ Le nom du client est obligatoire")
                else:
                    client_data = {
                        'nom': nom,
                        'adresse': adresse,
                        'ville': ville,
                        'province': province,
                        'code_postal': code_postal,
                        'telephone_bureau': telephone_bureau,
                        'telephone_cellulaire': telephone_cellulaire,
                        'email': email,
                        'contact_principal_nom': contact_nom,
                        'contact_principal_titre': contact_titre,
                        'contact_principal_telephone': contact_telephone,
                        'contact_principal_email': contact_email,
                        'notes': notes
                    }

                    client_id = save_client(
                        client_data,
                        client_a_modifier['id'] if client_a_modifier else None
                    )

                    if client_a_modifier:
                        st.success(f"✅ Client '{nom}' modifié avec succès!")
                        st.session_state.pop('client_a_modifier', None)
                    else:
                        st.success(f"✅ Client '{nom}' créé avec succès!")

                    st.rerun()


def get_client_selector(key_suffix="default"):
    """Widget de sélection de client pour les soumissions"""
    clients = get_all_clients()

    if not clients:
        st.warning("Aucun client enregistré. Créez d'abord un client dans la section 'Gestion des Clients'.")
        return None

    # Options de sélection
    options = ["Sélectionnez un client..."] + [f"{c['nom']} - {c['ville'] if c['ville'] else 'Ville non renseignée'}" for c in clients]

    selection = st.selectbox(
        "Client",
        options=options,
        key=f"client_selector_{key_suffix}",
        help="Sélectionnez un client existant ou créez-en un nouveau dans la section 'Gestion des Clients'"
    )

    if selection == "Sélectionnez un client...":
        return None

    # Trouver le client sélectionné
    index = options.index(selection) - 1
    return clients[index]


# Initialiser la base de données au chargement du module
init_clients_table()
