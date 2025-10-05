"""
Base de données pour la persistance des projets de métré TAKEOFF AI
Permet de sauvegarder et charger les projets de mesures PDF
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Définir le répertoire de données
DATA_DIR = os.getenv('DATA_DIR', 'data')
DB_PATH = os.path.join(DATA_DIR, 'takeoff_projects.db')


def init_takeoff_db():
    """Initialise la base de données Takeoff"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except PermissionError:
        pass  # Utiliser le répertoire courant si permission refusée

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table projets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_projet TEXT NOT NULL,
            client_id INTEGER,
            client_nom TEXT,
            pdf_nom TEXT,
            pdf_path TEXT,
            calibration_json TEXT,
            total_mesures INTEGER DEFAULT 0,
            total_montant REAL DEFAULT 0,
            notes TEXT,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
            date_modification TEXT DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'en_cours'
        )
    """)

    # Table mesures
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            label TEXT,
            value REAL,
            unit TEXT,
            page_number INTEGER DEFAULT 0,
            points_json TEXT,
            product_name TEXT,
            product_category TEXT,
            product_unit_price REAL,
            product_data_json TEXT,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Index pour performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_id ON measurements(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_statut ON projects(statut)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_date ON projects(date_modification)")

    conn.commit()
    conn.close()


def save_project(nom_projet: str, client_id: Optional[int] = None, client_nom: Optional[str] = None,
                 pdf_nom: Optional[str] = None, pdf_path: Optional[str] = None,
                 calibration: Optional[Dict] = None, notes: Optional[str] = None) -> int:
    """
    Sauvegarde un nouveau projet

    Args:
        nom_projet: Nom du projet
        client_id: ID du client (optionnel)
        client_nom: Nom du client (optionnel)
        pdf_nom: Nom du fichier PDF
        pdf_path: Chemin du fichier PDF
        calibration: Dictionnaire de calibration
        notes: Notes du projet

    Returns:
        ID du projet créé
    """
    init_takeoff_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO projects (nom_projet, client_id, client_nom, pdf_nom,
                             pdf_path, calibration_json, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nom_projet, client_id, client_nom, pdf_nom, pdf_path,
          json.dumps(calibration) if calibration else None, notes))

    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id


def update_project(project_id: int, nom_projet: Optional[str] = None,
                   client_nom: Optional[str] = None, notes: Optional[str] = None,
                   statut: Optional[str] = None):
    """
    Met à jour un projet existant

    Args:
        project_id: ID du projet
        nom_projet: Nouveau nom (optionnel)
        client_nom: Nouveau client (optionnel)
        notes: Nouvelles notes (optionnel)
        statut: Nouveau statut (optionnel)
    """
    init_takeoff_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updates = []
    params = []

    if nom_projet is not None:
        updates.append("nom_projet = ?")
        params.append(nom_projet)
    if client_nom is not None:
        updates.append("client_nom = ?")
        params.append(client_nom)
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)
    if statut is not None:
        updates.append("statut = ?")
        params.append(statut)

    if updates:
        updates.append("date_modification = CURRENT_TIMESTAMP")
        params.append(project_id)

        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()

    conn.close()


def save_measurement(project_id: int, measurement: Dict):
    """
    Sauvegarde une mesure dans un projet

    Args:
        project_id: ID du projet
        measurement: Dictionnaire contenant les données de la mesure
    """
    init_takeoff_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Extraire les données du produit
    product = measurement.get('product', {})
    product_name = product.get('name') if product else None
    product_category = product.get('category') if product else None
    product_unit_price = product.get('unit_price') if product else None

    cursor.execute("""
        INSERT INTO measurements (project_id, type, label, value, unit,
                                 page_number, points_json, product_name,
                                 product_category, product_unit_price, product_data_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        project_id,
        measurement.get('type'),
        measurement.get('label'),
        measurement.get('value'),
        measurement.get('unit'),
        measurement.get('page_number', 0),
        json.dumps(measurement.get('points', [])),
        product_name,
        product_category,
        product_unit_price,
        json.dumps(product) if product else None
    ))

    # Mettre à jour le compteur de mesures et le montant total
    cursor.execute("""
        UPDATE projects
        SET date_modification = CURRENT_TIMESTAMP,
            total_mesures = (SELECT COUNT(*) FROM measurements WHERE project_id = ?),
            total_montant = (
                SELECT COALESCE(SUM(value * product_unit_price), 0)
                FROM measurements
                WHERE project_id = ? AND product_unit_price IS NOT NULL
            )
        WHERE id = ?
    """, (project_id, project_id, project_id))

    conn.commit()
    conn.close()


def save_all_measurements(project_id: int, measurements: List[Dict]):
    """
    Sauvegarde toutes les mesures d'un projet (remplace les existantes)

    Args:
        project_id: ID du projet
        measurements: Liste des mesures
    """
    init_takeoff_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Supprimer les mesures existantes
    cursor.execute("DELETE FROM measurements WHERE project_id = ?", (project_id,))

    # Sauvegarder les nouvelles mesures
    for measurement in measurements:
        product = measurement.get('product', {})
        product_name = product.get('name') if product else None
        product_category = product.get('category') if product else None
        product_unit_price = product.get('unit_price') if product else None

        cursor.execute("""
            INSERT INTO measurements (project_id, type, label, value, unit,
                                     page_number, points_json, product_name,
                                     product_category, product_unit_price, product_data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            measurement.get('type'),
            measurement.get('label'),
            measurement.get('value'),
            measurement.get('unit'),
            measurement.get('page_number', 0),
            json.dumps(measurement.get('points', [])),
            product_name,
            product_category,
            product_unit_price,
            json.dumps(product) if product else None
        ))

    # Mettre à jour les totaux
    cursor.execute("""
        UPDATE projects
        SET date_modification = CURRENT_TIMESTAMP,
            total_mesures = (SELECT COUNT(*) FROM measurements WHERE project_id = ?),
            total_montant = (
                SELECT COALESCE(SUM(value * product_unit_price), 0)
                FROM measurements
                WHERE project_id = ? AND product_unit_price IS NOT NULL
            )
        WHERE id = ?
    """, (project_id, project_id, project_id))

    conn.commit()
    conn.close()


def get_all_projects(statut: Optional[str] = None, limit: int = 100) -> List[Tuple]:
    """
    Récupère tous les projets

    Args:
        statut: Filtrer par statut (optionnel)
        limit: Nombre maximum de projets à retourner

    Returns:
        Liste de tuples contenant les données des projets
    """
    init_takeoff_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if statut:
        cursor.execute("""
            SELECT id, nom_projet, client_nom, pdf_nom, total_mesures,
                   total_montant, date_creation, date_modification, statut
            FROM projects
            WHERE statut = ?
            ORDER BY date_modification DESC
            LIMIT ?
        """, (statut, limit))
    else:
        cursor.execute("""
            SELECT id, nom_projet, client_nom, pdf_nom, total_mesures,
                   total_montant, date_creation, date_modification, statut
            FROM projects
            ORDER BY date_modification DESC
            LIMIT ?
        """, (limit,))

    projects = cursor.fetchall()
    conn.close()
    return projects


def load_project(project_id: int) -> Optional[Dict]:
    """
    Charge un projet complet avec ses mesures

    Args:
        project_id: ID du projet

    Returns:
        Dictionnaire contenant le projet et ses mesures, ou None si non trouvé
    """
    init_takeoff_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Charger projet
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project_row = cursor.fetchone()

    if not project_row:
        conn.close()
        return None

    project = dict(project_row)

    # Charger mesures
    cursor.execute("""
        SELECT type, label, value, unit, page_number, points_json,
               product_name, product_category, product_unit_price, product_data_json
        FROM measurements
        WHERE project_id = ?
        ORDER BY id
    """, (project_id,))

    measurements = []
    for row in cursor.fetchall():
        measurement = {
            'type': row['type'],
            'label': row['label'],
            'value': row['value'],
            'unit': row['unit'],
            'page_number': row['page_number'],
            'points': json.loads(row['points_json']) if row['points_json'] else [],
            'product': json.loads(row['product_data_json']) if row['product_data_json'] else {}
        }
        measurements.append(measurement)

    conn.close()

    # Parser calibration JSON
    if project['calibration_json']:
        try:
            project['calibration'] = json.loads(project['calibration_json'])
        except:
            project['calibration'] = {'value': 1.0, 'unit': 'pi'}
    else:
        project['calibration'] = {'value': 1.0, 'unit': 'pi'}

    return {
        'project': project,
        'measurements': measurements
    }


def delete_project(project_id: int):
    """
    Supprime un projet et ses mesures (CASCADE)

    Args:
        project_id: ID du projet à supprimer
    """
    init_takeoff_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


def get_project_stats() -> Dict:
    """
    Récupère les statistiques globales des projets

    Returns:
        Dictionnaire avec les statistiques
    """
    init_takeoff_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_projects,
            SUM(total_mesures) as total_measurements,
            SUM(total_montant) as total_amount,
            COUNT(CASE WHEN statut = 'en_cours' THEN 1 END) as projects_en_cours,
            COUNT(CASE WHEN statut = 'termine' THEN 1 END) as projects_termines
        FROM projects
    """)

    row = cursor.fetchone()
    conn.close()

    return {
        'total_projects': row[0] or 0,
        'total_measurements': row[1] or 0,
        'total_amount': row[2] or 0.0,
        'projects_en_cours': row[3] or 0,
        'projects_termines': row[4] or 0
    }


def search_projects(search_term: str) -> List[Tuple]:
    """
    Recherche des projets par nom ou client

    Args:
        search_term: Terme de recherche

    Returns:
        Liste de projets correspondants
    """
    init_takeoff_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    search_pattern = f"%{search_term}%"
    cursor.execute("""
        SELECT id, nom_projet, client_nom, pdf_nom, total_mesures,
               total_montant, date_creation, date_modification, statut
        FROM projects
        WHERE nom_projet LIKE ? OR client_nom LIKE ?
        ORDER BY date_modification DESC
        LIMIT 50
    """, (search_pattern, search_pattern))

    projects = cursor.fetchall()
    conn.close()
    return projects
