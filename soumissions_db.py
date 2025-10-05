"""
Module de gestion de la base de données des soumissions pour EXPERTS IA
Permet la sauvegarde, consultation et gestion de l'historique des soumissions
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime

# Base de données pour les soumissions
DB_PATH = 'soumissions.db'


def generate_token():
    """Génère un token unique pour le lien public"""
    return str(uuid.uuid4())


def get_base_url():
    """Retourne l'URL de base de l'application selon l'environnement"""
    # Vérifier si une URL personnalisée est définie
    if os.getenv('APP_URL'):
        return os.getenv('APP_URL')
    # Vérifier si on est sur Hugging Face Spaces
    elif os.getenv('SPACE_ID') or os.getenv('SPACE_HOST'):
        space_host = os.getenv('SPACE_HOST')
        if space_host:
            return f"https://{space_host}"
        # Fallback: construire l'URL depuis SPACE_ID
        space_id = os.getenv('SPACE_ID', '')
        if space_id:
            return f"https://huggingface.co/spaces/{space_id}"
    # Vérifier Render
    elif os.getenv('RENDER'):
        render_url = os.getenv('RENDER_EXTERNAL_URL', '')
        if render_url:
            return render_url
    # Par défaut: localhost
    return "http://localhost:8501"


def init_soumissions_table():
    """Initialise la table des soumissions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS soumissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_soumission TEXT,
            client_id INTEGER,
            client_nom TEXT,
            projet_description TEXT,
            projet_type TEXT,
            projet_superficie REAL,
            conversation_id INTEGER,
            expert_profile TEXT,
            total_travaux REAL,
            administration REAL,
            contingences REAL,
            profit REAL,
            total_avant_taxes REAL,
            tps REAL,
            tvq REAL,
            investissement_total REAL,
            data_json TEXT,
            html_content TEXT,
            date_creation TEXT,
            date_modification TEXT,
            statut TEXT DEFAULT 'Brouillon',
            notes TEXT,
            token TEXT UNIQUE,
            lien_public TEXT,
            date_decision TEXT,
            signature_data TEXT,
            signature_nom TEXT,
            signature_date TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')

    # Ajouter les nouvelles colonnes si elles n'existent pas (migration)
    try:
        cursor.execute('ALTER TABLE soumissions ADD COLUMN token TEXT UNIQUE')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE soumissions ADD COLUMN lien_public TEXT')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE soumissions ADD COLUMN date_decision TEXT')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE soumissions ADD COLUMN signature_data TEXT')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE soumissions ADD COLUMN signature_nom TEXT')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE soumissions ADD COLUMN signature_date TEXT')
    except:
        pass

    # Index pour recherches rapides
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_nom ON soumissions(client_nom)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_numero ON soumissions(numero_soumission)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON soumissions(date_creation)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_statut ON soumissions(statut)')

    # Créer l'index token seulement si la colonne existe
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_token ON soumissions(token)')
    except:
        pass

    conn.commit()
    conn.close()
    print("[SOUMISSIONS DB] Table initialisée")


def save_soumission(data, html_content, client_id=None, conversation_id=None, expert_profile=None):
    """
    Sauvegarde une soumission dans la base de données

    Args:
        data: Dictionnaire de données extraites par l'IA
        html_content: Contenu HTML généré
        client_id: ID du client (optionnel)
        conversation_id: ID de la conversation (optionnel)
        expert_profile: Nom du profil expert (optionnel)

    Returns:
        int: ID de la soumission créée
    """
    init_soumissions_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Extraire les informations principales
    client = data.get('client', {})
    projet = data.get('projet', {})
    recap = data.get('recapitulatif', {})

    # Générer token et lien public
    token = generate_token()
    lien_public = f"{get_base_url()}/?token={token}"

    cursor.execute('''
        INSERT INTO soumissions (
            numero_soumission,
            client_id,
            client_nom,
            projet_description,
            projet_type,
            projet_superficie,
            conversation_id,
            expert_profile,
            total_travaux,
            administration,
            contingences,
            profit,
            total_avant_taxes,
            tps,
            tvq,
            investissement_total,
            data_json,
            html_content,
            date_creation,
            date_modification,
            statut,
            notes,
            token,
            lien_public
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('numero_soumission', 'AUTO'),
        client_id,
        client.get('nom', 'Non spécifié'),
        projet.get('description', ''),
        projet.get('type', 'Construction neuve'),
        projet.get('superficie_pi2', 0),
        conversation_id,
        expert_profile,
        recap.get('total_travaux', 0),
        recap.get('administration', 0),
        recap.get('contingences', 0),
        recap.get('profit', 0),
        recap.get('total_avant_taxes', 0),
        recap.get('tps', 0),
        recap.get('tvq', 0),
        recap.get('investissement_total', 0),
        json.dumps(data, ensure_ascii=False),
        html_content,
        now,
        now,
        'Brouillon',
        '',
        token,
        lien_public
    ))

    soumission_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Ajouter automatiquement l'événement au calendrier
    try:
        from calendar_manager import add_event
        from datetime import timedelta

        # Créer un événement de suivi dans 7 jours
        date_suivi = datetime.now() + timedelta(days=7)

        add_event(
            titre=f"Suivi soumission IA #{soumission_id}",
            description=f"Suivi automatique - Client: {client.get('nom', 'N/A')} - Projet: {projet.get('description', 'N/A')[:50]}",
            date_debut=date_suivi,
            type_event='soumission',
            reference_id=f"SOU-IA-{soumission_id}",
            client_nom=client.get('nom', ''),
            statut='en_attente',
            couleur='#3b82f6'
        )
    except Exception as e:
        print(f"Erreur ajout calendrier soumission IA: {e}")

    print(f"[SOUMISSIONS DB] Soumission #{soumission_id} sauvegardée")
    return soumission_id


def get_all_soumissions(limit=50, statut=None):
    """
    Récupère toutes les soumissions

    Args:
        limit: Nombre maximum de résultats
        statut: Filtrer par statut (Brouillon, Envoyée, Acceptée, Refusée)

    Returns:
        list: Liste de dictionnaires de soumissions
    """
    init_soumissions_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if statut:
        cursor.execute('''
            SELECT id, numero_soumission, client_nom, projet_description, projet_type,
                   projet_superficie, investissement_total, date_creation, statut
            FROM soumissions
            WHERE statut = ?
            ORDER BY date_creation DESC
            LIMIT ?
        ''', (statut, limit))
    else:
        cursor.execute('''
            SELECT id, numero_soumission, client_nom, projet_description, projet_type,
                   projet_superficie, investissement_total, date_creation, statut
            FROM soumissions
            ORDER BY date_creation DESC
            LIMIT ?
        ''', (limit,))

    colonnes = ['id', 'numero_soumission', 'client_nom', 'projet_description', 'projet_type',
                'projet_superficie', 'investissement_total', 'date_creation', 'statut']
    soumissions = []

    for row in cursor.fetchall():
        soumission = dict(zip(colonnes, row))
        soumissions.append(soumission)

    conn.close()
    return soumissions


def get_soumission_by_id(soumission_id):
    """
    Récupère une soumission complète par son ID

    Args:
        soumission_id: ID de la soumission

    Returns:
        dict: Soumission complète avec data_json et html_content
    """
    init_soumissions_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM soumissions WHERE id = ?', (soumission_id,))
    colonnes = [description[0] for description in cursor.description]
    row = cursor.fetchone()

    conn.close()

    if row:
        soumission = dict(zip(colonnes, row))
        # Décoder le JSON
        if soumission.get('data_json'):
            soumission['data'] = json.loads(soumission['data_json'])
        return soumission
    return None


def update_soumission_statut(soumission_id, statut, notes=''):
    """
    Met à jour le statut d'une soumission

    Args:
        soumission_id: ID de la soumission
        statut: Nouveau statut (Brouillon, Envoyée, Acceptée, Refusée)
        notes: Notes optionnelles
    """
    init_soumissions_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        UPDATE soumissions
        SET statut = ?, notes = ?, date_modification = ?
        WHERE id = ?
    ''', (statut, notes, now, soumission_id))

    conn.commit()
    conn.close()
    print(f"[SOUMISSIONS DB] Soumission #{soumission_id} statut → {statut}")


def delete_soumission(soumission_id):
    """Supprime une soumission de la base de données"""
    init_soumissions_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM soumissions WHERE id = ?', (soumission_id,))

    conn.commit()
    conn.close()
    print(f"[SOUMISSIONS DB] Soumission #{soumission_id} supprimée")


def get_soumissions_stats():
    """
    Retourne des statistiques sur les soumissions

    Returns:
        dict: Statistiques (total, par statut, montant total, etc.)
    """
    init_soumissions_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    stats = {}

    # Nombre total
    cursor.execute('SELECT COUNT(*) FROM soumissions')
    stats['total'] = cursor.fetchone()[0]

    # Par statut
    cursor.execute('''
        SELECT statut, COUNT(*), SUM(investissement_total)
        FROM soumissions
        GROUP BY statut
    ''')
    stats['par_statut'] = {}
    for statut, count, total in cursor.fetchall():
        stats['par_statut'][statut] = {
            'count': count,
            'total': total or 0
        }

    # Montant total toutes soumissions
    cursor.execute('SELECT SUM(investissement_total) FROM soumissions')
    stats['montant_total'] = cursor.fetchone()[0] or 0

    # Montant moyen
    if stats['total'] > 0:
        stats['montant_moyen'] = stats['montant_total'] / stats['total']
    else:
        stats['montant_moyen'] = 0

    conn.close()
    return stats


def get_soumission_by_token(token):
    """
    Récupère une soumission par son token (pour lien public)

    Args:
        token: Token unique de la soumission

    Returns:
        dict: Soumission complète ou None
    """
    init_soumissions_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM soumissions WHERE token = ?', (token,))
    colonnes = [description[0] for description in cursor.description]
    row = cursor.fetchone()

    conn.close()

    if row:
        soumission = dict(zip(colonnes, row))
        # Décoder le JSON
        if soumission.get('data_json'):
            soumission['data'] = json.loads(soumission['data_json'])
        return soumission
    return None


def update_soumission_decision(token, action, signature_data=None, signature_nom=None):
    """
    Met à jour la décision du client (Acceptée/Refusée) avec signature

    Args:
        token: Token de la soumission
        action: 'approve' ou 'reject'
        signature_data: Données de la signature (base64)
        signature_nom: Nom du signataire

    Returns:
        bool: True si succès
    """
    init_soumissions_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    nouveau_statut = 'Acceptée' if action == 'approve' else 'Refusée'

    cursor.execute('''
        UPDATE soumissions
        SET statut = ?,
            date_decision = ?,
            date_modification = ?,
            signature_data = ?,
            signature_nom = ?,
            signature_date = ?
        WHERE token = ?
    ''', (nouveau_statut, now, now, signature_data, signature_nom, now, token))

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    if success:
        print(f"[SOUMISSIONS DB] Soumission avec token {token[:8]}... → {nouveau_statut}")

    return success


# Initialiser la table au chargement du module
init_soumissions_table()
