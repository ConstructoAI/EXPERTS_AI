"""
Module de création de bons de commande simplifié
Interface avec tableau direct comme Excel
"""

import streamlit as st
import json
import uuid
from datetime import datetime, date
import sqlite3
import os
import pandas as pd

# Import du gestionnaire de fournisseurs
try:
    from fournisseurs_manager import (
        init_fournisseurs_db,
        get_fournisseurs_list,
        get_fournisseur_by_nom
    )
    FOURNISSEURS_AVAILABLE = True
except ImportError:
    FOURNISSEURS_AVAILABLE = False

# Import des utilitaires de nommage
try:
    from filename_utils import generate_bon_commande_filename
except ImportError:
    def generate_bon_commande_filename(numero, fournisseur_nom, extension='.html', date=None):
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%Y-%m-%d')
        fournisseur_clean = ''.join(c for c in fournisseur_nom if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_').lower()
        if not fournisseur_clean:
            fournisseur_clean = 'fournisseur'
        if not extension.startswith('.'):
            extension = '.' + extension
        return f"boncommande_{numero}_{fournisseur_clean}_{date_str}{extension}"

# Import de la configuration d'entreprise
try:
    from entreprise_config import get_entreprise_config
    DYNAMIC_CONFIG = True
except ImportError:
    DYNAMIC_CONFIG = False

def get_company_info():
    """Récupère les informations de l'entreprise"""
    if DYNAMIC_CONFIG:
        config = get_entreprise_config()
        return {
            'name': config.get('nom', 'Entreprise'),
            'address': config.get('adresse', ''),
            'city': config.get('ville', 'Montréal'),
            'province': config.get('province', 'Québec'),
            'postal_code': config.get('code_postal', ''),
            'phone': config.get('telephone_bureau', ''),
            'email': config.get('email', ''),
            'rbq': config.get('rbq', ''),
            'neq': config.get('neq', ''),
            'tps': config.get('tps', ''),
            'tvq': config.get('tvq', '')
        }
    else:
        return {
            'name': 'Construction Excellence Plus',
            'address': '2500 Boulevard Innovation',
            'city': 'Montréal',
            'province': 'Québec',
            'postal_code': 'H3K 2A9',
            'phone': '514-555-8900',
            'email': 'info@constructionexcellence.ca',
            'rbq': '1234-5678-01',
            'neq': '1234567890',
            'tps': '123456789RT0001',
            'tvq': '1234567890TQ0001'
        }

def get_base_url():
    """Retourne l'URL de base de l'application selon l'environnement"""
    if os.getenv('APP_URL'):
        return os.getenv('APP_URL')
    # Vérifier si on est sur Hugging Face Spaces
    elif os.getenv('SPACE_ID') or os.getenv('SPACE_HOST'):
        # Récupérer l'URL Hugging Face depuis les variables d'environnement
        space_host = os.getenv('SPACE_HOST')
        if space_host:
            return f"https://{space_host}"
        # Fallback: construire l'URL depuis SPACE_ID
        space_id = os.getenv('SPACE_ID')
        if space_id:
            # Format: username-spacename
            return f"https://huggingface.co/spaces/{space_id}"
        # Si rien ne fonctionne, utiliser votre URL connue
        return 'https://huggingface.co/spaces/Sylvainleduc/C2B'
    # Sinon, vérifier si on est sur Render
    elif os.getenv('RENDER'):
        # URL de production sur Render
        return 'https://c2b-heritage.onrender.com'
    else:
        # Développement local
        return 'http://localhost:8501'

def get_db_path():
    """Retourne le chemin correct de la base de données"""
    # Utiliser un chemin relatif au répertoire courant
    data_dir = os.getenv('DATA_DIR', 'data')

    # Créer le dossier data s'il n'existe pas (avec gestion d'erreur)
    try:
        os.makedirs(data_dir, exist_ok=True)
    except PermissionError:
        # Si permission refusée, utiliser le répertoire courant
        data_dir = '.'

    return os.path.join(data_dir, 'bons_commande_simple.db')

def init_bon_commande_db():
    """Initialise la base de données"""
    db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bons_commande (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fournisseur_nom TEXT,
            client_nom TEXT,
            projet_nom TEXT,
            items_json TEXT,
            sous_total REAL,
            tps REAL,
            tvq REAL,
            total REAL,
            statut TEXT DEFAULT 'brouillon',
            token TEXT UNIQUE,
            lien_public TEXT
        )
    ''')

    conn.commit()
    conn.close()

def generate_numero_bon():
    """Génère un numéro unique de bon de commande"""
    current_year = datetime.now().year
    db_path = get_db_path()

    # S'assurer que la base existe
    init_bon_commande_db()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT numero FROM bons_commande
        WHERE numero LIKE ?
        ORDER BY numero DESC
        LIMIT 1
    ''', (f'BC-{current_year}-%',))

    result = cursor.fetchone()
    conn.close()

    if result:
        try:
            last_num = int(result[0].split('-')[-1])
            return f"BC-{current_year}-{last_num + 1:03d}"
        except:
            pass

    return f"BC-{current_year}-001"

def save_bon_commande(data):
    """Sauvegarde le bon de commande"""
    init_bon_commande_db()

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    token = str(uuid.uuid4())
    base_url = get_base_url()
    lien_public = f"{base_url}/?token={token}&type=bon_commande"

    cursor.execute('''
        INSERT INTO bons_commande
        (numero, fournisseur_nom, client_nom, projet_nom, items_json,
         sous_total, tps, tvq, total, token, lien_public)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['numero'],
        data['fournisseur']['nom'],
        data['client']['nom'],
        data['projet']['nom'],
        json.dumps(data['items'], ensure_ascii=False),
        data['totaux']['sous_total'],
        data['totaux']['tps'],
        data['totaux']['tvq'],
        data['totaux']['total'],
        token,
        lien_public
    ))

    conn.commit()
    bon_id = cursor.lastrowid
    conn.close()

    # Ajouter automatiquement l'événement au calendrier
    try:
        from calendar_manager import add_event
        from datetime import datetime, timedelta

        # Si date de livraison fournie, l'utiliser, sinon dans 14 jours
        date_livraison = data.get('date_livraison')
        if not date_livraison:
            date_livraison = datetime.now() + timedelta(days=14)

        add_event(
            titre=f"Livraison BC {data['numero']}",
            description=f"Livraison prévue - Fournisseur: {data['fournisseur']['nom']} - Total: {data['totaux']['total']:.2f}$",
            date_debut=date_livraison,
            type_event='livraison',
            reference_id=data['numero'],
            client_nom=data['client']['nom'],
            statut='en_attente',
            couleur='#06b6d4'
        )
    except Exception as e:
        print(f"Erreur ajout calendrier bon commande: {e}")

    # Générer le nom de fichier
    filename = generate_bon_commande_filename(
        data['numero'],
        data['fournisseur']['nom']
    )

    return bon_id, token, lien_public, filename

def generate_modern_html_embedded(data, company):
    """Template moderne intégré directement pour garantir la disponibilité"""
    # Créer le tableau des items avec un design amélioré
    items_html = ""
    for i, item in enumerate(data['items'], 1):
        row_class = 'row-even' if i % 2 == 0 else 'row-odd'
        items_html += f"""
        <tr class="{row_class}">
            <td class="item-number">{i}</td>
            <td class="item-description">
                <div class="item-title">{item['description']}</div>
                {f'<div class="item-details">{item["details"]}</div>' if item.get('details') else ''}
            </td>
            <td class="item-qty">{item['quantite']}</td>
            <td class="item-unit">{item['unite']}</td>
            <td class="item-price">{item['prix_unitaire']:,.2f} $</td>
            <td class="item-total">{item['total']:,.2f} $</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bon de Commande {data['numero']}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}

            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
                animation: slideIn 0.5s ease-out;
            }}

            @keyframes slideIn {{
                from {{
                    opacity: 0;
                    transform: translateY(30px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}

            .header {{
                background: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
                color: white;
                padding: 40px;
                position: relative;
                overflow: hidden;
            }}

            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
                background-size: 20px 20px;
                animation: moveGrid 20s linear infinite;
            }}

            @keyframes moveGrid {{
                0% {{ transform: translate(0, 0); }}
                100% {{ transform: translate(20px, 20px); }}
            }}

            .header-content {{
                position: relative;
                z-index: 1;
            }}

            .header h1 {{
                font-size: 36px;
                font-weight: 700;
                margin-bottom: 15px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                letter-spacing: 2px;
            }}

            .header .numero {{
                font-size: 24px;
                font-weight: 500;
                padding: 10px 20px;
                background: rgba(255,255,255,0.2);
                border-radius: 50px;
                display: inline-block;
                backdrop-filter: blur(10px);
            }}

            .status-badge {{
                position: absolute;
                top: 40px;
                right: 40px;
                background: rgba(255,255,255,0.2);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                backdrop-filter: blur(10px);
            }}

            .section {{
                padding: 30px 40px;
                border-bottom: 1px solid #f1f5f9;
            }}

            .section-title {{
                font-size: 14px;
                font-weight: 700;
                color: #3B82F6;
                margin-bottom: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                position: relative;
                padding-left: 15px;
            }}

            .section-title::before {{
                content: '';
                position: absolute;
                left: 0;
                top: 50%;
                transform: translateY(-50%);
                width: 4px;
                height: 20px;
                background: linear-gradient(135deg, #3B82F6, #1F2937);
                border-radius: 2px;
            }}

            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
            }}

            .info-item {{
                display: flex;
                align-items: flex-start;
                gap: 12px;
                padding: 12px;
                background: #f8fafc;
                border-radius: 10px;
                transition: all 0.3s ease;
            }}

            .info-item:hover {{
                background: #f1f5f9;
                transform: translateX(5px);
            }}

            .info-icon {{
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #3B82F6, #1F2937);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 20px;
                flex-shrink: 0;
            }}

            .info-content {{
                flex: 1;
            }}

            .info-label {{
                font-size: 12px;
                font-weight: 500;
                color: #64748b;
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            .info-value {{
                font-size: 15px;
                color: #1e293b;
                font-weight: 600;
            }}

            table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
            }}

            thead {{
                background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            }}

            th {{
                padding: 16px;
                text-align: left;
                font-weight: 700;
                font-size: 12px;
                color: #475569;
                text-transform: uppercase;
                letter-spacing: 1px;
                border-bottom: 2px solid #e2e8f0;
            }}

            tbody tr {{
                transition: all 0.3s ease;
            }}

            tbody tr:hover {{
                background: #f8fafc;
                transform: scale(1.01);
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }}

            .row-even {{
                background: #fafbfc;
            }}

            td {{
                padding: 16px;
                border-bottom: 1px solid #f1f5f9;
                color: #334155;
            }}

            .item-number {{
                text-align: center;
                font-weight: 700;
                color: #3B82F6;
                font-size: 16px;
            }}

            .item-title {{
                font-weight: 600;
                color: #1e293b;
                font-size: 15px;
                margin-bottom: 4px;
            }}

            .item-details {{
                font-size: 13px;
                color: #64748b;
                line-height: 1.5;
            }}

            .item-qty, .item-unit {{
                text-align: center;
                font-weight: 500;
            }}

            .item-price {{
                text-align: right;
                font-weight: 500;
                color: #475569;
            }}

            .item-total {{
                text-align: right;
                font-weight: 700;
                color: #3B82F6;
                font-size: 16px;
            }}

            .totals {{
                background: linear-gradient(135deg, #f8fafc, #f1f5f9);
                padding: 30px 40px;
            }}

            .totals-container {{
                max-width: 400px;
                margin-left: auto;
            }}

            .total-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 20px;
                margin-bottom: 8px;
                background: white;
                border-radius: 10px;
                transition: all 0.3s ease;
            }}

            .total-row:hover {{
                transform: translateX(-5px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }}

            .total-label {{
                font-weight: 500;
                color: #64748b;
                font-size: 14px;
            }}

            .total-value {{
                font-weight: 600;
                color: #334155;
                font-size: 16px;
            }}

            .grand-total {{
                background: linear-gradient(135deg, #3B82F6, #1F2937);
                color: white;
                padding: 16px 24px;
                margin-top: 16px;
                transform: scale(1.02);
                box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
            }}

            .grand-total .total-label {{
                color: white;
                font-size: 16px;
                font-weight: 600;
            }}

            .grand-total .total-value {{
                color: white;
                font-size: 24px;
                font-weight: 700;
            }}

            .footer {{
                background: linear-gradient(135deg, #1e293b, #334155);
                color: white;
                padding: 30px 40px;
                text-align: center;
            }}

            @media print {{
                body {{
                    background: white;
                    padding: 0;
                }}
                .container {{
                    box-shadow: none;
                    border-radius: 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="status-badge">📋 BON DE COMMANDE</div>
                <div class="header-content">
                    <h1>BON DE COMMANDE</h1>
                    <div class="numero">{data['numero']}</div>
                    <div style="margin-top: 15px; font-size: 16px;">📅 {data['date']}</div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Informations de l'Émetteur</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-icon">🏢</div>
                        <div class="info-content">
                            <div class="info-label">Entreprise</div>
                            <div class="info-value">{company['name']}</div>
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="info-icon">📍</div>
                        <div class="info-content">
                            <div class="info-label">Adresse</div>
                            <div class="info-value">{company['address']}, {company['city']}</div>
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="info-icon">📞</div>
                        <div class="info-content">
                            <div class="info-label">Téléphone</div>
                            <div class="info-value">{company['phone']}</div>
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="info-icon">✉️</div>
                        <div class="info-content">
                            <div class="info-label">Courriel</div>
                            <div class="info-value">{company['email']}</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Fournisseur</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-icon">🏭</div>
                        <div class="info-content">
                            <div class="info-label">Nom du Fournisseur</div>
                            <div class="info-value">{data['fournisseur']['nom']}</div>
                        </div>
                    </div>
                    {f'''<div class="info-item">
                        <div class="info-icon">👤</div>
                        <div class="info-content">
                            <div class="info-label">Contact</div>
                            <div class="info-value">{data['fournisseur']['contact']}</div>
                        </div>
                    </div>''' if data['fournisseur'].get('contact') else ''}
                    {f'''<div class="info-item">
                        <div class="info-icon">📱</div>
                        <div class="info-content">
                            <div class="info-label">Téléphone</div>
                            <div class="info-value">{data['fournisseur']['telephone']}</div>
                        </div>
                    </div>''' if data['fournisseur'].get('telephone') else ''}
                    {f'''<div class="info-item">
                        <div class="info-icon">📧</div>
                        <div class="info-content">
                            <div class="info-label">Courriel</div>
                            <div class="info-value">{data['fournisseur']['email']}</div>
                        </div>
                    </div>''' if data['fournisseur'].get('email') else ''}
                </div>
            </div>

            <div class="section">
                <div class="section-title">Détails du Projet</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-icon">👥</div>
                        <div class="info-content">
                            <div class="info-label">Client</div>
                            <div class="info-value">{data['client']['nom']}</div>
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="info-icon">🏗️</div>
                        <div class="info-content">
                            <div class="info-label">Nom du Projet</div>
                            <div class="info-value">{data['projet']['nom']}</div>
                        </div>
                    </div>
                    {f'''<div class="info-item">
                        <div class="info-icon">📌</div>
                        <div class="info-content">
                            <div class="info-label">Adresse</div>
                            <div class="info-value">{data['projet']['adresse']}</div>
                        </div>
                    </div>''' if data['projet'].get('adresse') else ''}
                </div>
            </div>

            <div class="section">
                <div class="section-title">Articles Commandés</div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 5%; text-align: center;">#</th>
                            <th style="width: 45%;">Description</th>
                            <th style="width: 10%; text-align: center;">Quantité</th>
                            <th style="width: 10%; text-align: center;">Unité</th>
                            <th style="width: 15%; text-align: right;">Prix Unitaire</th>
                            <th style="width: 15%; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
            </div>

            <div class="totals">
                <div class="totals-container">
                    <div class="total-row">
                        <span class="total-label">Sous-total</span>
                        <span class="total-value">{data['totaux']['sous_total']:,.2f} $</span>
                    </div>
                    <div class="total-row">
                        <span class="total-label">TPS (5%)</span>
                        <span class="total-value">{data['totaux']['tps']:,.2f} $</span>
                    </div>
                    <div class="total-row">
                        <span class="total-label">TVQ (9.975%)</span>
                        <span class="total-value">{data['totaux']['tvq']:,.2f} $</span>
                    </div>
                    <div class="total-row grand-total">
                        <span class="total-label">MONTANT TOTAL</span>
                        <span class="total-value">{data['totaux']['total']:,.2f} $</span>
                    </div>
                </div>
            </div>

            <div class="footer">
                <div style="font-size: 18px; font-weight: 600; margin-bottom: 20px;">✨ Merci pour votre collaboration!</div>
                <div style="opacity: 0.9;">
                    {company['name']} | {company['phone']} | {company['email']}<br>
                    RBQ: {company['rbq']} | NEQ: {company['neq']}<br>
                    TPS: {company['tps']} | TVQ: {company['tvq']}
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# Import du template style soumission
try:
    from bon_commande_template_soumission import generate_soumission_style_html
    USE_SOUMISSION_TEMPLATE = True
except ImportError as e:
    USE_SOUMISSION_TEMPLATE = False
    # Essayer le template moderne comme fallback
    try:
        from bon_commande_template_moderne import generate_modern_html
        USE_MODERN_TEMPLATE = True
    except:
        USE_MODERN_TEMPLATE = False

def generate_html(data):
    """Génère le HTML du bon de commande"""
    company = get_company_info()

    # Utiliser le template style soumission en priorité
    if USE_SOUMISSION_TEMPLATE:
        try:
            return generate_soumission_style_html(data, company)
        except Exception as e:
            st.warning(f"⚠️ Erreur avec le template soumission: {e}")

    # Sinon essayer le template moderne
    if 'USE_MODERN_TEMPLATE' in globals() and USE_MODERN_TEMPLATE:
        try:
            return generate_modern_html(data, company)
        except Exception as e:
            st.warning(f"⚠️ Erreur avec le template moderne: {e}")

    # En dernier recours, utiliser le template intégré
    return generate_modern_html_embedded(data, company)

    # Créer le tableau des items
    items_html = ""
    for i, item in enumerate(data['items'], 1):
        items_html += f"""
        <tr>
            <td style="text-align: center; font-weight: 600; color: #3B82F6;">{i}</td>
            <td>
                <div style="font-weight: 600;">{item['description']}</div>
                {f'<div style="font-size: 12px; color: #64748b; margin-top: 4px;">{item["details"]}</div>' if item.get('details') else ''}
            </td>
            <td style="text-align: center;">{item['quantite']}</td>
            <td style="text-align: center;">{item['unite']}</td>
            <td style="text-align: right;">{item['prix_unitaire']:,.2f} $</td>
            <td style="text-align: right; font-weight: 600;">{item['total']:,.2f} $</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bon de Commande {data['numero']}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Inter', sans-serif;
                background: #FAFBFF;
                padding: 20px;
                color: #1F2937;
            }}

            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                overflow: hidden;
            }}

            .header {{
                background: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}

            .header h1 {{
                font-size: 28px;
                margin-bottom: 10px;
                letter-spacing: 1px;
            }}

            .header .numero {{
                font-size: 18px;
                opacity: 0.95;
            }}

            .section {{
                padding: 25px 30px;
                border-bottom: 1px solid #e5e7eb;
            }}

            .section-title {{
                font-size: 16px;
                font-weight: 600;
                color: #4b5563;
                margin-bottom: 15px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            .info-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }}

            .info-item {{
                display: flex;
                gap: 8px;
            }}

            .info-label {{
                font-weight: 500;
                color: #6b7280;
                min-width: 100px;
            }}

            .info-value {{
                color: #1f2937;
            }}

            .table-container {{
                padding: 0;
                overflow-x: auto;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th {{
                background: #FAFBFF;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                font-size: 13px;
                color: #1F2937;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 2px solid #E5E7EB;
            }}

            td {{
                padding: 14px 12px;
                border-bottom: 1px solid #E5E7EB;
            }}

            tr:hover {{
                background: #FAFBFF;
            }}

            .totals {{
                background: #FAFBFF;
                padding: 20px 30px;
            }}

            .totals-content {{
                max-width: 350px;
                margin-left: auto;
            }}

            .total-row {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                font-size: 15px;
            }}

            .total-row.grand-total {{
                font-size: 20px;
                font-weight: 700;
                color: #3B82F6;
                border-top: 2px solid #E5E7EB;
                margin-top: 10px;
                padding-top: 12px;
            }}

            .footer {{
                background: #1F2937;
                color: white;
                padding: 20px 30px;
                text-align: center;
                font-size: 13px;
            }}

            .remove-btn {{
                background: #ef4444;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
            }}

            .add-btn {{
                background: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                margin: 15px 30px;
            }}

            @media print {{
                body {{
                    background: white;
                    padding: 0;
                }}

                .container {{
                    box-shadow: none;
                }}

                .remove-btn, .add-btn {{
                    display: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>BON DE COMMANDE</h1>
                <div class="numero">{data['numero']}</div>
                <div style="margin-top: 8px; opacity: 0.9;">
                    {datetime.now().strftime('%d/%m/%Y')}
                </div>
            </div>

            <div class="section">
                <div class="section-title">Entreprise</div>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">Nom:</span>
                        <span class="info-value">{company['name']}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Téléphone:</span>
                        <span class="info-value">{company['phone']}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Adresse:</span>
                        <span class="info-value">{company['address']}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Courriel:</span>
                        <span class="info-value">{company['email']}</span>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Fournisseur</div>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">Nom:</span>
                        <span class="info-value">{data['fournisseur']['nom']}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Contact:</span>
                        <span class="info-value">{data['fournisseur'].get('contact', '')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Téléphone:</span>
                        <span class="info-value">{data['fournisseur'].get('telephone', '')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Courriel:</span>
                        <span class="info-value">{data['fournisseur'].get('email', '')}</span>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Projet</div>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">Client:</span>
                        <span class="info-value">{data['client']['nom']}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Projet:</span>
                        <span class="info-value">{data['projet']['nom']}</span>
                    </div>
                </div>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50px; text-align: center;">Item</th>
                            <th>Description</th>
                            <th style="width: 80px; text-align: center;">Quantité</th>
                            <th style="width: 80px; text-align: center;">Unité</th>
                            <th style="width: 120px; text-align: right;">Prix unitaire</th>
                            <th style="width: 120px; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
            </div>

            <div class="totals">
                <div class="totals-content">
                    <div class="total-row">
                        <span>Sous-total:</span>
                        <span>{data['totaux']['sous_total']:,.2f} $</span>
                    </div>
                    <div class="total-row">
                        <span>TPS (5%):</span>
                        <span>{data['totaux']['tps']:,.2f} $</span>
                    </div>
                    <div class="total-row">
                        <span>TVQ (9.975%):</span>
                        <span>{data['totaux']['tvq']:,.2f} $</span>
                    </div>
                    <div class="total-row grand-total">
                        <span>TOTAL:</span>
                        <span>{data['totaux']['total']:,.2f} $</span>
                    </div>
                </div>
            </div>

            <div class="footer">
                <p>{company['name']} | RBQ: {company['rbq']} | NEQ: {company['neq']}</p>
                <p style="margin-top: 8px; opacity: 0.8;">
                    Conditions: Net 30 jours | Validité: 30 jours
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html

def show_bon_commande_interface():
    """Interface principale pour la création de bons de commande"""
    show_bon_commande_simple()

def show_bon_commande_simple():
    """Interface simplifiée pour créer un bon de commande"""

    # Initialiser la base de données au démarrage
    init_bon_commande_db()

    # Vérifier si le gestionnaire de fournisseurs doit être affiché
    if st.session_state.get('show_fournisseurs_manager', False):
        from fournisseurs_manager import show_fournisseurs_interface

        # Afficher le bouton retour
        if st.button("⬅️ Retour au Bon de Commande"):
            st.session_state.show_fournisseurs_manager = False
            st.rerun()

        # Afficher l'interface de gestion
        show_fournisseurs_interface()
        return  # Arrêter l'exécution ici pour ne pas afficher le reste

    st.header("📋 Créer un Bon de Commande")

    # Initialiser la session state
    if 'bon_items' not in st.session_state:
        st.session_state.bon_items = []

    if 'bon_numero' not in st.session_state:
        st.session_state.bon_numero = generate_numero_bon()

    # Informations de base en colonnes
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"📌 Numéro: **{st.session_state.bon_numero}**")

    with col2:
        date_bon = st.date_input("📅 Date", value=date.today(), key="date_bon")

    with col3:
        statut = st.selectbox("📊 Statut", ["Brouillon", "Envoyé", "Approuvé"], key="statut_bon")

    st.divider()

    # Informations du fournisseur et projet
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Fournisseur")

        # Si le module fournisseurs est disponible, utiliser la liste déroulante
        if FOURNISSEURS_AVAILABLE:
            # Initialiser la base de données des fournisseurs
            init_fournisseurs_db()

            # Options de sélection
            col_select, col_new = st.columns([3, 1])

            with col_select:
                # Récupérer la liste des fournisseurs
                fournisseurs_list = get_fournisseurs_list()
                fournisseurs_options = ["🆕 Nouveau fournisseur..."] + fournisseurs_list

                selected_fournisseur = st.selectbox(
                    "Sélectionner un fournisseur *",
                    options=fournisseurs_options,
                    key="select_fournisseur",
                    help="Choisissez dans la liste ou créez un nouveau"
                )

            with col_new:
                if st.button("🏢 Gérer", help="Ouvrir le gestionnaire de fournisseurs", key="btn_gerer_fournisseurs"):
                    st.session_state.show_fournisseurs_manager = True

            # Si un fournisseur existant est sélectionné, récupérer ses infos
            if selected_fournisseur and selected_fournisseur != "🆕 Nouveau fournisseur...":
                fournisseur_data = get_fournisseur_by_nom(selected_fournisseur)

                if fournisseur_data:
                    # Afficher les informations en lecture seule
                    st.success(f"✅ Informations chargées pour: {selected_fournisseur}")

                    # Stocker les données dans des variables
                    fournisseur_nom = fournisseur_data['nom']
                    fournisseur_contact = fournisseur_data['contact_principal'] or ""
                    fournisseur_tel = fournisseur_data['telephone'] or ""
                    fournisseur_email = fournisseur_data['email'] or ""

                    # Afficher les infos en lecture seule
                    st.text_input("Nom du fournisseur", value=fournisseur_nom, disabled=True, key="fournisseur_nom_display")
                    st.text_input("Contact", value=fournisseur_contact, disabled=True, key="fournisseur_contact_display")
                    st.text_input("Téléphone", value=fournisseur_tel, disabled=True, key="fournisseur_tel_display")
                    st.text_input("Courriel", value=fournisseur_email, disabled=True, key="fournisseur_email_display")

                    # Afficher les infos supplémentaires si disponibles
                    if fournisseur_data.get('adresse'):
                        with st.expander("Informations complètes"):
                            col_info1, col_info2 = st.columns(2)

                            with col_info1:
                                st.write("**Adresse:**")
                                st.write(fournisseur_data.get('adresse', ''))
                                st.write(f"{fournisseur_data.get('ville', '')}, {fournisseur_data.get('province', '')}")
                                st.write(fournisseur_data.get('code_postal', ''))

                            with col_info2:
                                if fournisseur_data.get('rbq'):
                                    st.write(f"**RBQ:** {fournisseur_data['rbq']}")
                                if fournisseur_data.get('conditions_paiement'):
                                    st.write(f"**Conditions:** {fournisseur_data['conditions_paiement']}")
                                if fournisseur_data.get('delai_livraison'):
                                    st.write(f"**Délai:** {fournisseur_data['delai_livraison']}")
                else:
                    st.error("Erreur lors du chargement des informations")
                    fournisseur_nom = selected_fournisseur
                    fournisseur_contact = ""
                    fournisseur_tel = ""
                    fournisseur_email = ""
            else:
                # Nouveau fournisseur - champs éditables
                st.info("🆕 Entrez les informations du nouveau fournisseur")
                fournisseur_nom = st.text_input("Nom du fournisseur *", key="fournisseur_nom_new")
                fournisseur_contact = st.text_input("Personne contact", key="fournisseur_contact_new")
                fournisseur_tel = st.text_input("Téléphone", key="fournisseur_tel_new")
                fournisseur_email = st.text_input("Courriel", key="fournisseur_email_new")

                if st.checkbox("Sauvegarder ce fournisseur pour réutilisation", key="save_new_fournisseur"):
                    st.info("💾 Le fournisseur sera sauvegardé lors de la création du bon de commande")
        else:
            # Mode classique sans base de données
            fournisseur_nom = st.text_input("Nom du fournisseur *", key="fournisseur_nom")
            fournisseur_contact = st.text_input("Personne contact", key="fournisseur_contact")
            fournisseur_tel = st.text_input("Téléphone", key="fournisseur_tel")
            fournisseur_email = st.text_input("Courriel", key="fournisseur_email")

    with col2:
        st.subheader("📁 Projet")
        client_nom = st.text_input("Nom du client *", key="client_nom")
        projet_nom = st.text_input("Nom du projet *", key="projet_nom")
        projet_adresse = st.text_input("Adresse du projet", key="projet_adresse")
        ref_soumission = st.text_input("Réf. soumission", key="ref_soumission")

    st.divider()

    # Section Articles - Tableau simple
    st.subheader("📦 Articles")

    # Formulaire d'ajout d'article
    with st.expander("➕ **Ajouter un article**", expanded=True):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            new_description = st.text_input("Description", key="new_desc")
            new_details = st.text_area("Détails (optionnel)", key="new_details", height=60)

        with col2:
            new_quantite = st.number_input("Quantité", min_value=0.0, value=1.0, step=0.5, key="new_qty")

        with col3:
            new_unite = st.selectbox("Unité", ["unité", "m²", "m³", "ml", "kg", "h", "jour"], key="new_unit")

        with col4:
            new_prix = st.number_input("Prix unitaire ($)", min_value=0.0, value=0.0, step=10.0, key="new_price")

        if st.button("➕ Ajouter l'article", type="primary", key="btn_ajouter_article"):
            if new_description and new_quantite > 0 and new_prix > 0:
                st.session_state.bon_items.append({
                    'description': new_description,
                    'details': new_details,
                    'quantite': new_quantite,
                    'unite': new_unite,
                    'prix_unitaire': new_prix,
                    'total': new_quantite * new_prix
                })
                st.rerun()
            else:
                st.warning("Veuillez remplir tous les champs obligatoires")

    # Afficher le tableau des articles
    if st.session_state.bon_items:
        st.markdown("### 📊 Tableau des articles")

        # Créer un DataFrame pour l'affichage
        df_display = []
        for i, item in enumerate(st.session_state.bon_items):
            df_display.append({
                'Item': i + 1,
                'Description': item['description'],
                'Quantité': item['quantite'],
                'Unité': item['unite'],
                'Prix unitaire': f"{item['prix_unitaire']:,.2f} $",
                'Total': f"{item['total']:,.2f} $"
            })

        # Afficher le tableau
        df = pd.DataFrame(df_display)
        st.dataframe(df, hide_index=True)

        # Boutons de suppression pour chaque ligne
        st.markdown("#### 🗑️ Supprimer des articles")
        cols = st.columns(6)
        for i, item in enumerate(st.session_state.bon_items):
            with cols[i % 6]:
                if st.button(f"❌ Item {i+1}", key=f"del_{i}"):
                    st.session_state.bon_items.pop(i)
                    st.rerun()

        # Calculer les totaux
        sous_total = sum(item['total'] for item in st.session_state.bon_items)
        tps = sous_total * 0.05
        tvq = sous_total * 0.09975
        total = sous_total + tps + tvq

        # Afficher le récapitulatif
        st.divider()
        st.markdown("### 📊 RÉCAPITULATIF")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Sous-total", f"{sous_total:,.2f} $")

        with col2:
            st.metric("TPS (5%)", f"{tps:,.2f} $")

        with col3:
            st.metric("TVQ (9.975%)", f"{tvq:,.2f} $")

        with col4:
            st.metric("**TOTAL**", f"**{total:,.2f} $**")

        # Boutons d'action
        st.divider()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("💾 Sauvegarder", type="primary", key="btn_sauvegarder_bon"):
                # Sauvegarder le nouveau fournisseur si demandé
                if (FOURNISSEURS_AVAILABLE and
                    st.session_state.get('save_new_fournisseur', False) and
                    st.session_state.get('select_fournisseur') == "🆕 Nouveau fournisseur..."):
                    try:
                        from fournisseurs_manager import save_fournisseur
                        new_fournisseur_data = {
                            'nom': fournisseur_nom,
                            'type': 'Fournisseur',
                            'contact_principal': fournisseur_contact,
                            'telephone': fournisseur_tel,
                            'email': fournisseur_email,
                            'actif': 1
                        }
                        save_fournisseur(new_fournisseur_data)
                        st.success(f"✅ Fournisseur '{fournisseur_nom}' ajouté à la base de données")
                    except Exception as e:
                        st.warning(f"Impossible de sauvegarder le fournisseur: {e}")

                if fournisseur_nom and client_nom and projet_nom:
                    # Préparer les données
                    data = {
                        'numero': st.session_state.bon_numero,
                        'date': str(date_bon),
                        'fournisseur': {
                            'nom': fournisseur_nom,
                            'contact': fournisseur_contact,
                            'telephone': fournisseur_tel,
                            'email': fournisseur_email
                        },
                        'client': {
                            'nom': client_nom
                        },
                        'projet': {
                            'nom': projet_nom,
                            'adresse': projet_adresse,
                            'ref_soumission': ref_soumission
                        },
                        'items': st.session_state.bon_items,
                        'totaux': {
                            'sous_total': sous_total,
                            'tps': tps,
                            'tvq': tvq,
                            'total': total
                        }
                    }

                    try:
                        bon_id, token, lien, filename = save_bon_commande(data)
                        st.success(f"✅ Bon de commande sauvegardé!")
                        st.info(f"📄 Fichier: {filename}")
                        st.code(lien)
                    except Exception as e:
                        st.error(f"Erreur: {e}")
                else:
                    st.warning("Veuillez remplir les champs obligatoires (Fournisseur, Client, Projet)")

        with col2:
            # Générer l'aperçu HTML
            if fournisseur_nom:
                data = {
                    'numero': st.session_state.bon_numero,
                    'date': str(date_bon),
                    'fournisseur': {
                        'nom': fournisseur_nom,
                        'contact': fournisseur_contact,
                        'telephone': fournisseur_tel,
                        'email': fournisseur_email
                    },
                    'client': {
                        'nom': client_nom or "À définir"
                    },
                    'projet': {
                        'nom': projet_nom or "À définir",
                        'adresse': projet_adresse,
                        'ref_soumission': ref_soumission
                    },
                    'items': st.session_state.bon_items,
                    'totaux': {
                        'sous_total': sous_total,
                        'tps': tps,
                        'tvq': tvq,
                        'total': total
                    }
                }

                html_content = generate_html(data)
                filename = generate_bon_commande_filename(
                    st.session_state.bon_numero,
                    fournisseur_nom
                )

                st.download_button(
                    label="📥 Télécharger HTML",
                    data=html_content,
                    file_name=filename,
                    mime="text/html"
                )

        with col3:
            if st.button("👁️ Aperçu", key="btn_apercu_bon"):
                with st.expander("Aperçu du bon de commande", expanded=True):
                    st.components.v1.html(html_content, height=800, scrolling=True)

        with col4:
            if st.button("🔄 Nouveau", key="btn_nouveau_bon"):
                st.session_state.bon_items = []
                st.session_state.bon_numero = generate_numero_bon()
                for key in ['fournisseur_nom', 'fournisseur_contact', 'fournisseur_tel',
                           'fournisseur_email', 'client_nom', 'projet_nom',
                           'projet_adresse', 'ref_soumission']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    else:
        st.info("👆 Ajoutez des articles pour commencer")

# Point d'entrée pour l'importation
if __name__ == "__main__":
    st.set_page_config(page_title="Bon de Commande Simple", page_icon="📋", layout="wide")
    show_bon_commande_interface()
