"""
Module de création de soumissions budgétaires personnalisables
Support multi-entreprises avec configuration dynamique
"""

import streamlit as st
import json
import uuid
from datetime import datetime, date
import sqlite3
import os

# Import du module de configuration d'entreprise
try:
    from entreprise_config import (
        get_entreprise_config, 
        get_formatted_company_info,
        get_company_colors,
        get_company_logo,
        get_commercial_params
    )
    DYNAMIC_CONFIG = True
except ImportError:
    DYNAMIC_CONFIG = False
    # Configuration par défaut si le module n'est pas disponible
    COMPANY_INFO = {
        'name': 'Construction Excellence Plus',
        'address': '2500 Boulevard Innovation',
        'city': 'Montréal (Québec) H3K 2A9',
        'phone': '514-555-8900',
        'cell': '514-555-8901',
        'email': 'info@constructionexcellence.ca',
        'rbq': '1234-5678-01',
        'neq': '1234567890',
        'tps': '123456789RT0001',
        'tvq': '1234567890TQ0001'
    }

def get_company_info():
    """Récupère les informations de l'entreprise depuis la configuration"""
    if DYNAMIC_CONFIG:
        config = get_entreprise_config()
        return {
            'name': config.get('nom', 'Entreprise'),
            'address': config.get('adresse', ''),
            'city': f"{config.get('ville', '')} ({config.get('province', 'Québec')}) {config.get('code_postal', '')}",
            'phone': config.get('telephone_bureau', ''),
            'cell': config.get('telephone_cellulaire', ''),
            'email': config.get('email', ''),
            'rbq': config.get('rbq', ''),
            'neq': config.get('neq', ''),
            'tps': config.get('tps', ''),
            'tvq': config.get('tvq', '')
        }
    else:
        return COMPANY_INFO

# Import des catégories complètes si disponible, sinon utiliser les catégories par défaut
try:
    from categories_complete import CATEGORIES_COMPLETE
    CATEGORIES = CATEGORIES_COMPLETE
except ImportError:
    # Catégories complètes détaillées intégrées directement
    CATEGORIES = {
        '0': {
            'name': '0.0 - Travaux Préparatoires et Démolition',
            'items': [
                {'id': '0-1', 'title': 'Permis et études',
                 'description': 'Permis de construction, étude géotechnique, certificat de localisation, test de percolation (si requis).'},
                {'id': '0-2', 'title': 'Démolition et décontamination',
                 'description': 'Démolition de structures existantes, décontamination (amiante, vermiculite si applicable), disposition des débris.'},
                {'id': '0-3', 'title': 'Préparation du terrain et services temporaires',
                 'description': 'Déboisement, essouchement, nivellement, protection des arbres, électricité temporaire, toilette de chantier, clôture.'}
            ]
        },
        '1': {
            'name': '1.0 - Fondation, Infrastructure et Services',
            'items': [
                {'id': '1-1', 'title': 'Excavation et remblai',
                 'description': 'Excavation générale, remblai granulaire compacté, pierre concassée, membrane géotextile.'},
                {'id': '1-2', 'title': 'Fondation complète',
                 'description': 'Béton 30 MPA, armature 15M, coffrage, coulée, finition, cure, isolant R-10 sous-dalle, pare-vapeur.'},
                {'id': '1-3', 'title': 'Drainage et imperméabilisation',
                 'description': 'Drain français, membrane d\'imperméabilisation, panneau de drainage, pompe de puisard.'},
                {'id': '1-4', 'title': 'Raccordements et services',
                 'description': 'Égout, aqueduc, pluvial (jusqu\'à 50\'), système septique si applicable (fosse et champ selon Q-2, r.22).'}
            ]
        },
        '2': {
            'name': '2.0 - Structure et Charpente',
            'items': [
                {'id': '2-1', 'title': 'Structure de plancher',
                 'description': 'Poutrelles ajourées 14", solives de rive, contreventement, sous-plancher 3/4" collé-vissé.'},
                {'id': '2-2', 'title': 'Murs porteurs et cloisons',
                 'description': 'Montants 2x6 @ 16" c/c murs extérieurs, 2x4 @ 16" c/c cloisons, lisses, sablières doubles, linteaux.'},
                {'id': '2-3', 'title': 'Structure de toit',
                 'description': 'Fermes préfabriquées ou chevrons/solives selon plans, contreventement, support de toit 5/8".'},
                {'id': '2-4', 'title': 'Éléments structuraux spéciaux',
                 'description': 'Poutres et colonnes d\'acier, poutres LVL, colonnes décoratives, quincaillerie structurale.'}
            ]
        },
        '3': {
            'name': '3.0 - Enveloppe Extérieure',
            'items': [
                {'id': '3-1', 'title': 'Toiture - Matériaux',
                 'description': 'Bardeaux architecturaux 30 ans, membrane autocollante, papier #15, ventilation de toit, évents de plomberie.'},
                {'id': '3-2', 'title': 'Toiture - Main-d\'œuvre et ferblanterie',
                 'description': 'Installation bardeaux, solins, noues, faîtières, gouttières 5", descentes pluviales, protège-gouttières.'},
                {'id': '3-3', 'title': 'Revêtements muraux - Matériaux',
                 'description': 'Maçonnerie, fibrociment, vinyle/acier, fourrures, pare-air Tyvek, solins.'},
                {'id': '3-4', 'title': 'Revêtements muraux - Main-d\'œuvre',
                 'description': 'Installation complète des revêtements, calfeutrage, scellants, finition des coins et jonctions.'},
                {'id': '3-5', 'title': 'Portes et fenêtres',
                 'description': 'Fenêtres PVC/hybride, double vitrage Low-E argon, portes extérieures, porte patio, portes de garage isolées.'},
                {'id': '3-6', 'title': 'Soffites, fascias et accessoires',
                 'description': 'Soffites ventilés aluminium, fascias aluminium, moulures de finition, ventilation d\'entretoit.'},
                {'id': '3-7', 'title': 'Structures extérieures',
                 'description': 'Balcons, terrasses, garde-corps aluminium/verre, escaliers extérieurs, auvents, pergola.'},
                {'id': '3-8', 'title': 'Maçonnerie décorative et cheminée',
                 'description': 'Cheminée préfabriquée, revêtement de pierre/brique, couronnement, chapeau de cheminée.'}
            ]
        },
        '4': {
            'name': '4.0 - Systèmes Mécaniques et Électriques',
            'items': [
                {'id': '4-1', 'title': 'Plomberie - Distribution et drainage',
                 'description': 'Tuyauterie PEX/cuivre, drainage ABS, valves d\'arrêt, clapets antiretour, supports et isolant de tuyaux.'},
                {'id': '4-2', 'title': 'Plomberie - Appareils et accessoires',
                 'description': 'Salles de bain complètes, évier cuisine double, chauffe-eau, adoucisseur d\'eau, robinetterie extérieure.'},
                {'id': '4-3', 'title': 'Chauffage au sol (si applicable)',
                 'description': 'Plancher radiant multi-zones, chaudière haute efficacité, pompes de circulation, contrôles.'},
                {'id': '4-4', 'title': 'Électricité - Distribution principale',
                 'description': 'Panneau 200A/40 circuits, mise à terre, câblage principal, sous-panneau garage, protection surtension.'},
                {'id': '4-5', 'title': 'Électricité - Filage et dispositifs',
                 'description': 'Câblage complet Romex, prises multiples, interrupteurs, circuits dédiés, prises DDFT, détecteurs.'},
                {'id': '4-6', 'title': 'Éclairage et contrôles',
                 'description': 'Luminaires encastrés, éclairage sous-armoires, gradateurs, éclairage extérieur, commandes intelligentes.'},
                {'id': '4-7', 'title': 'CVAC - Équipements principaux',
                 'description': 'Thermopompe centrale, fournaise d\'appoint gaz/électrique, humidificateur, filtre HEPA.'},
                {'id': '4-8', 'title': 'CVAC - Distribution et ventilation',
                 'description': 'Conduits isolés, grilles et diffuseurs, VRC/VRE, ventilateurs salles de bain, hotte cuisine.'},
                {'id': '4-9', 'title': 'Systèmes spécialisés',
                 'description': 'Pré-filage alarme/caméras, aspirateur central, audio intégré, réseau informatique Cat6, borne VÉ 240V.'}
            ]
        },
        '5': {
            'name': '5.0 - Isolation et Étanchéité',
            'items': [
                {'id': '5-1', 'title': 'Isolation thermique',
                 'description': 'Murs ext. R-24.5, plafond cathédrale R-31, grenier R-50, sous-sol R-20, solives de rive R-20.'},
                {'id': '5-2', 'title': 'Étanchéité à l\'air',
                 'description': 'Pare-vapeur 6 mil, scellant acoustique, ruban Tuck Tape, mousse expansive, coupe-froid.'},
                {'id': '5-3', 'title': 'Insonorisation',
                 'description': 'Laine acoustique entre étages, barres résilientes, scellant acoustique, isolant plomberie.'},
                {'id': '5-4', 'title': 'Tests et certification',
                 'description': 'Test d\'infiltrométrie, thermographie, certification Novoclimat Select, rapport de conformité.'}
            ]
        },
        '6': {
            'name': '6.0 - Finitions Intérieures',
            'items': [
                {'id': '6-1', 'title': 'Cloisons sèches - Gypse',
                 'description': 'Gypse 1/2" régulier et hydrofuge, gypse 5/8" plafonds, coins métalliques, finition niveau 4.'},
                {'id': '6-2', 'title': 'Peinture et finition murale',
                 'description': 'Apprêt, peinture 2 couches (murs/plafonds), peinture émail (boiseries), papier-peint si applicable.'},
                {'id': '6-3', 'title': 'Revêtements de plancher',
                 'description': 'Bois franc/ingénierie, céramique, tapis, vinyle luxe, sous-planchers adaptés.'},
                {'id': '6-4', 'title': 'Carrelage et dosseret',
                 'description': 'Céramique salles de bain (plancher/murs douche), dosseret cuisine, membrane Schluter, joints époxy.'},
                {'id': '6-5', 'title': 'Ébénisterie - Cuisine',
                 'description': 'Armoires thermoplastique/bois, comptoir quartz/granit, îlot, pantry, quincaillerie soft-close.'},
                {'id': '6-6', 'title': 'Ébénisterie - Salles de bain et autres',
                 'description': 'Vanités salles de bain, lingerie, walk-in aménagé, rangement entrée, bureau intégré.'},
                {'id': '6-7', 'title': 'Menuiserie intérieure',
                 'description': 'Portes intérieures, cadres et moulures, plinthes, cimaises, tablettes décoratives.'},
                {'id': '6-8', 'title': 'Escaliers et rampes',
                 'description': 'Escaliers bois franc/MDF, main courante, barreaux métal/bois, poteaux décoratifs.'},
                {'id': '6-9', 'title': 'Finition sous-sol (si applicable)',
                 'description': 'Divisions, isolation, gypse, plancher flottant/époxy, plafond suspendu, salle mécanique finie.'},
                {'id': '6-10', 'title': 'Accessoires et quincaillerie',
                 'description': 'Poignées de porte, crochets, barres à serviettes, miroirs, tablettes garde-robes, cache-radiateurs.'}
            ]
        },
        '7': {
            'name': '7.0 - Aménagement Extérieur et Garage',
            'items': [
                {'id': '7-1', 'title': 'Terrassement et nivellement',
                 'description': 'Nivellement final, terre végétale, ensemencement gazon, arbres et arbustes de base.'},
                {'id': '7-2', 'title': 'Surfaces dures',
                 'description': 'Entrée asphalte/pavé uni, trottoirs béton/pavé, bordures, patio béton/composite.'},
                {'id': '7-3', 'title': 'Clôtures et structures',
                 'description': 'Clôture selon type, portail, muret décoratif, pergola, cabanon préfabriqué.'},
                {'id': '7-4', 'title': 'Éclairage extérieur et irrigation',
                 'description': 'Éclairage paysager, lampadaires, système d\'irrigation si applicable, minuteries.'},
                {'id': '7-5', 'title': 'Finition garage',
                 'description': 'Dalle béton finie, murs gypse peint, éclairage, prises électriques, rangement, porte de service.'}
            ]
        }
    }

def create_soumission_form():
    """Crée le formulaire de soumission interactif"""
    
    st.markdown("""
    <style>
        .soumission-header {
            background: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .category-section {
            background: #FAFBFF;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid #3B82F6;
        }
        .item-row {
            padding: 0.5rem;
            margin: 0.5rem 0;
            background: white;
            border-radius: 4px;
        }
        .total-box {
            background: linear-gradient(135deg, #FAFBFF 0%, #E5E7EB 100%);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3B82F6;
            margin: 20px 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialiser session state pour la soumission
    if 'soumission_data' not in st.session_state:
        st.session_state.soumission_data = {
            'numero': generate_numero_soumission(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'client': {},
            'projet': {},
            'items': {},
            'totaux': {},
            'conditions': [],
            'exclusions': []
        }
    
    # Récupérer le nom de l'entreprise
    company_name = get_company_info()['name']
    
    st.markdown('<div class="soumission-header">', unsafe_allow_html=True)
    st.title("🏗️ CRÉATION DE SOUMISSION MANUELLE")
    st.markdown(f"### {company_name}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabs pour organiser le formulaire
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Informations", "🏗️ Travaux", "💰 Récapitulatif", "💾 Actions"])
    
    with tab1:
        st.markdown("### Informations du projet")
        
        # Sélecteur de client
        st.markdown("#### 👤 Sélection du client")

        # Importer la fonction de sélection de client
        try:
            from client_config import get_client_selector

            # Afficher le sélecteur de client
            selected_client = get_client_selector(key_suffix="heritage")

            # Si un client est sélectionné, pré-remplir les champs
            if selected_client:
                if st.button("📋 Utiliser les infos de ce client", key="use_client_heritage"):
                    st.session_state.soumission_data['client']['nom'] = selected_client.get('nom', '')
                    st.session_state.soumission_data['client']['adresse'] = selected_client.get('adresse', '')
                    st.session_state.soumission_data['client']['ville'] = selected_client.get('ville', '')
                    st.session_state.soumission_data['client']['code_postal'] = selected_client.get('code_postal', '')
                    # Utiliser téléphone bureau en priorité, sinon téléphone cellulaire
                    st.session_state.soumission_data['client']['telephone'] = (
                        selected_client.get('telephone_bureau', '') or
                        selected_client.get('telephone_cellulaire', '')
                    )
                    st.session_state.soumission_data['client']['courriel'] = selected_client.get('email', '')
                    st.success("✅ Informations du client chargées!")
                    st.rerun()
        except ImportError:
            st.info("💡 Module de gestion des clients non disponible")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 👤 Information client")
            st.session_state.soumission_data['client']['nom'] = st.text_input(
                "Nom du client",
                value=st.session_state.soumission_data['client'].get('nom', '')
            )
            st.session_state.soumission_data['client']['adresse'] = st.text_input(
                "Adresse",
                value=st.session_state.soumission_data['client'].get('adresse', '')
            )
            st.session_state.soumission_data['client']['ville'] = st.text_input(
                "Ville",
                value=st.session_state.soumission_data['client'].get('ville', '')
            )
            st.session_state.soumission_data['client']['code_postal'] = st.text_input(
                "Code postal",
                value=st.session_state.soumission_data['client'].get('code_postal', '')
            )
            st.session_state.soumission_data['client']['telephone'] = st.text_input(
                "Téléphone",
                value=st.session_state.soumission_data['client'].get('telephone', '')
            )
            st.session_state.soumission_data['client']['courriel'] = st.text_input(
                "Courriel",
                value=st.session_state.soumission_data['client'].get('courriel', '')
            )
        
        with col2:
            st.markdown("#### 🏠 Information projet")
            st.session_state.soumission_data['projet']['nom'] = st.text_input(
                "Nom du projet",
                value=st.session_state.soumission_data['projet'].get('nom', '')
            )
            st.session_state.soumission_data['projet']['adresse'] = st.text_input(
                "Adresse du projet",
                value=st.session_state.soumission_data['projet'].get('adresse', '')
            )
            st.session_state.soumission_data['projet']['type'] = st.selectbox(
                "Type de construction",
                ["Résidentielle", "Commerciale", "Rénovation", "Agrandissement"]
            )
            col_a, col_b = st.columns(2)
            with col_a:
                st.session_state.soumission_data['projet']['superficie'] = st.number_input(
                    "Superficie (pi²)",
                    min_value=0,
                    value=st.session_state.soumission_data['projet'].get('superficie', 0)
                )
            with col_b:
                st.session_state.soumission_data['projet']['etages'] = st.number_input(
                    "Nombre d'étages",
                    min_value=1,
                    max_value=5,
                    value=st.session_state.soumission_data['projet'].get('etages', 1)
                )
            
            date_debut = st.date_input(
                "Date de début prévue",
                value=date.today()
            )
            # Convertir la date en string pour éviter les problèmes de sérialisation
            st.session_state.soumission_data['projet']['date_debut'] = date_debut.isoformat()
            st.session_state.soumission_data['projet']['duree'] = st.text_input(
                "Durée estimée",
                value=st.session_state.soumission_data['projet'].get('duree', '3-4 mois')
            )
    
    with tab2:
        st.markdown("### Détails des travaux")
        
        # Style pour les tableaux et champs éditables
        st.markdown("""
        <style>
            .stNumberInput > div > div > input {
                text-align: right;
            }
            .category-header {
                background: #FAFBFF;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
            .item-table {
                width: 100%;
                margin: 10px 0;
            }
            /* Style pour les champs de texte dans les colonnes */
            .stTextInput > div > div > input {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                font-weight: 600;
            }
            .stTextArea > div > div > textarea {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                font-size: 0.9em;
                min-height: 50px !important;
            }
            /* Hover effect pour les champs éditables */
            .stTextInput > div > div > input:hover,
            .stTextArea > div > div > textarea:hover {
                background-color: #ffffff;
                border-color: #4b5563;
            }
            .stTextInput > div > div > input:focus,
            .stTextArea > div > div > textarea:focus {
                background-color: #ffffff;
                border-color: #4b5563;
                box-shadow: 0 0 0 0.2rem rgba(75, 85, 99, 0.25);
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Mode admin pour calculs automatiques
        admin_mode = st.checkbox("Calcul automatique du total (Quantité × Coût unitaire)", value=True)
        
        # Pour chaque catégorie
        for cat_id, category in CATEGORIES.items():
            with st.expander(f"**{category['name']}**", expanded=False):
                
                # Bouton de réinitialisation pour toute la catégorie
                if st.button(f"🔄 Réinitialiser toute la catégorie", key=f"reset_cat_{cat_id}", help="Réinitialiser tous les titres et descriptions aux valeurs par défaut"):
                    for item in category['items']:
                        item_key = f"{cat_id}_{item['id']}"
                        # S'assurer que l'item existe dans session_state
                        if item_key not in st.session_state.soumission_data['items']:
                            st.session_state.soumission_data['items'][item_key] = {}
                        # Réinitialiser les valeurs
                        st.session_state.soumission_data['items'][item_key]['titre'] = item['title']
                        st.session_state.soumission_data['items'][item_key]['description'] = item['description']
                    
                    # Incrémenter le compteur pour forcer le refresh de tous les widgets
                    if 'reset_counter' not in st.session_state:
                        st.session_state['reset_counter'] = 0
                    st.session_state['reset_counter'] += 1
                    
                    st.rerun()
                
                # Header du tableau
                col_headers = st.columns([3.2, 1, 1.5, 1.5, 0.8])
                with col_headers[0]:
                    st.markdown("**Description**")
                with col_headers[1]:
                    st.markdown("**Quantité**")
                with col_headers[2]:
                    st.markdown("**Coût unitaire**")
                with col_headers[3]:
                    st.markdown("**Total**")
                with col_headers[4]:
                    st.markdown("**Actions**")
                
                st.markdown("---")
                
                category_total = 0
                
                # Afficher les items prédéfinis
                for item in category['items']:
                    item_key = f"{cat_id}_{item['id']}"
                    
                    # Colonnes pour chaque ligne d'item (ajustées pour accommoder les 2 boutons)
                    col1, col2, col3, col4, col5 = st.columns([3.2, 1, 1.5, 1.5, 0.8])
                    
                    with col1:
                        # Vérifier si on doit utiliser les valeurs par défaut ou personnalisées
                        # S'assurer que 'items' existe
                        if 'items' not in st.session_state.soumission_data:
                            st.session_state.soumission_data['items'] = {}
                        stored_data = st.session_state.soumission_data['items'].get(item_key, {})
                        
                        # Titre éditable - utiliser la valeur stockée ou par défaut
                        current_title = stored_data.get('titre', item['title'])
                        custom_title = st.text_input(
                            "Titre",
                            value=current_title,
                            key=f"title_{item_key}_{st.session_state.get('reset_counter', 0)}",  # Ajouter un compteur pour forcer le refresh
                            label_visibility="collapsed",
                            placeholder="Titre de l'item"
                        )
                        
                        # Description éditable - utiliser la valeur stockée ou par défaut
                        current_description = stored_data.get('description', item['description'])
                        custom_description = st.text_area(
                            "Description",
                            value=current_description,
                            key=f"desc_{item_key}_{st.session_state.get('reset_counter', 0)}",  # Ajouter un compteur pour forcer le refresh
                            label_visibility="collapsed",
                            height=60,
                            placeholder="Description détaillée"
                        )
                    
                    with col2:
                        qty = st.number_input(
                            "Quantité",
                            min_value=0.0,
                            value=st.session_state.soumission_data['items'].get(item_key, {}).get('quantite', 1.0),
                            step=1.0,
                            key=f"qty_{item_key}",
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        unit_price = st.number_input(
                            "Coût unitaire",
                            min_value=0.0,
                            value=st.session_state.soumission_data['items'].get(item_key, {}).get('prix_unitaire', 0.0),
                            format="%.2f",
                            step=100.0,
                            key=f"unit_{item_key}",
                            label_visibility="collapsed"
                        )
                    
                    # Calcul du montant total
                    if admin_mode:
                        amount = qty * unit_price
                        with col4:
                            st.markdown(f"<div style='text-align: right; font-weight: bold; padding: 8px; background: #FAFBFF; border-radius: 4px;'>${amount:,.2f}</div>", unsafe_allow_html=True)
                    else:
                        with col4:
                            amount = st.number_input(
                                "Total",
                                min_value=0.0,
                                value=st.session_state.soumission_data['items'].get(item_key, {}).get('montant', 0.0),
                                format="%.2f",
                                step=100.0,
                                key=f"amount_{item_key}",
                                label_visibility="collapsed"
                            )
                    
                    with col5:
                        # Créer un conteneur pour les boutons d'action
                        action_container = st.container()
                        with action_container:
                            # Utiliser des colonnes pour aligner les boutons
                            col5a, col5b = st.columns(2)
                            
                            with col5a:
                                # Bouton de réinitialisation du texte
                                if st.button("🔄", key=f"reset_{item_key}", help="Réinitialiser le titre et la description aux valeurs par défaut"):
                                    # Réinitialiser uniquement le titre et la description
                                    if item_key not in st.session_state.soumission_data['items']:
                                        st.session_state.soumission_data['items'][item_key] = {}
                                    
                                    # Mettre les valeurs par défaut
                                    st.session_state.soumission_data['items'][item_key]['titre'] = item['title']
                                    st.session_state.soumission_data['items'][item_key]['description'] = item['description']
                                    
                                    # Incrémenter le compteur pour forcer le refresh des widgets
                                    if 'reset_counter' not in st.session_state:
                                        st.session_state['reset_counter'] = 0
                                    st.session_state['reset_counter'] += 1
                                    
                                    st.rerun()
                            
                            with col5b:
                                # Bouton pour effacer les montants
                                if st.button("🗑️", key=f"del_{item_key}", help="Effacer les montants"):
                                    qty = 0
                                    unit_price = 0
                                    amount = 0
                    
                    # Sauvegarder les données de l'item avec les valeurs personnalisées
                    st.session_state.soumission_data['items'][item_key] = {
                        'titre': custom_title,
                        'description': custom_description,
                        'quantite': qty,
                        'prix_unitaire': unit_price,
                        'montant': amount
                    }
                    
                    category_total += amount
                    
                    # Ligne de séparation subtile
                    st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)
                
                # Section pour ajouter des items personnalisés
                st.markdown("---")
                
                # Bouton pour ajouter une ligne personnalisée
                with st.container():
                    st.markdown("#### ➕ Ajouter une ligne personnalisée")
                    
                    # Initialiser les items personnalisés pour cette catégorie si nécessaire
                    custom_items_key = f"custom_items_{cat_id}"
                    if custom_items_key not in st.session_state:
                        st.session_state[custom_items_key] = []
                    
                    # Formulaire pour ajouter un nouvel item
                    col_add1, col_add2 = st.columns([3, 1])
                    
                    with col_add1:
                        new_item_title = st.text_input(
                            "Titre du nouvel item",
                            key=f"new_title_{cat_id}",
                            placeholder="Ex: Travaux supplémentaires"
                        )
                    
                    with col_add2:
                        if st.button("➕ Ajouter", key=f"add_btn_{cat_id}"):
                            if new_item_title:
                                # Générer un ID unique pour le nouvel item
                                import uuid
                                new_item_id = str(uuid.uuid4())[:8]
                                st.session_state[custom_items_key].append({
                                    'id': new_item_id,
                                    'title': new_item_title
                                })
                                st.rerun()
                    
                    # Afficher les items personnalisés
                    for custom_item in st.session_state.get(custom_items_key, []):
                        item_key = f"{cat_id}_custom_{custom_item['id']}"
                        
                        col1, col2, col3, col4, col5 = st.columns([3.2, 1, 1.5, 1.5, 0.8])
                        
                        with col1:
                            # Titre éditable
                            custom_title = st.text_input(
                                "Titre",
                                value=st.session_state.soumission_data['items'].get(item_key, {}).get('titre', custom_item['title']),
                                key=f"title_{item_key}",
                                label_visibility="collapsed",
                                placeholder="Titre de l'item"
                            )
                            # Description éditable
                            custom_description = st.text_area(
                                "Description",
                                value=st.session_state.soumission_data['items'].get(item_key, {}).get('description', ''),
                                key=f"desc_{item_key}",
                                label_visibility="collapsed",
                                height=60,
                                placeholder="Description détaillée"
                            )
                        
                        with col2:
                            qty = st.number_input(
                                "Quantité",
                                min_value=0.0,
                                value=st.session_state.soumission_data['items'].get(item_key, {}).get('quantite', 1.0),
                                step=1.0,
                                key=f"qty_{item_key}",
                                label_visibility="collapsed"
                            )
                        
                        with col3:
                            unit_price = st.number_input(
                                "Coût unitaire",
                                min_value=0.0,
                                value=st.session_state.soumission_data['items'].get(item_key, {}).get('prix_unitaire', 0.0),
                                format="%.2f",
                                step=100.0,
                                key=f"unit_{item_key}",
                                label_visibility="collapsed"
                            )
                        
                        # Calcul du montant total
                        if admin_mode:
                            amount = qty * unit_price
                            with col4:
                                st.markdown(f"<div style='text-align: right; font-weight: bold; padding: 8px; background: #FAFBFF; border-radius: 4px;'>${amount:,.2f}</div>", unsafe_allow_html=True)
                        else:
                            with col4:
                                amount = st.number_input(
                                    "Total",
                                    min_value=0.0,
                                    value=st.session_state.soumission_data['items'].get(item_key, {}).get('montant', 0.0),
                                    format="%.2f",
                                    step=100.0,
                                    key=f"amount_{item_key}",
                                    label_visibility="collapsed"
                                )
                        
                        with col5:
                            # Bouton pour supprimer l'item personnalisé
                            if st.button("🗑️", key=f"del_custom_{item_key}", help="Supprimer cette ligne"):
                                st.session_state[custom_items_key] = [
                                    item for item in st.session_state[custom_items_key] 
                                    if item['id'] != custom_item['id']
                                ]
                                if item_key in st.session_state.soumission_data['items']:
                                    del st.session_state.soumission_data['items'][item_key]
                                st.rerun()
                        
                        # Sauvegarder les données de l'item personnalisé
                        st.session_state.soumission_data['items'][item_key] = {
                            'titre': custom_title,
                            'description': custom_description,
                            'quantite': qty,
                            'prix_unitaire': unit_price,
                            'montant': amount
                        }
                        
                        category_total += amount
                
                # Afficher le sous-total de la catégorie
                st.markdown("---")
                st.markdown(f"<div style='text-align: right; font-size: 1.1em; font-weight: bold; color: #1F2937;'>Sous-total de la catégorie: ${category_total:,.2f}</div>", unsafe_allow_html=True)
        
        # Paramètres des taux
        st.markdown("### ⚙️ Paramètres des taux")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            profit = st.slider("Profit (%)", 0, 50, 15) / 100
        with col2:
            admin = st.slider("Administration (%)", 0, 10, 3) / 100
        with col3:
            contingency = st.slider("Contingences (%)", 0, 25, 12) / 100
        
        st.session_state.soumission_data['taux'] = {
            'profit': profit,
            'admin': admin,
            'contingency': contingency
        }
    
    with tab3:
        st.markdown("### 📊 Récapitulatif financier")
        
        # Calculer les totaux
        total_travaux = sum(
            item.get('montant', 0) 
            for item in st.session_state.soumission_data['items'].values()
        )
        
        taux = st.session_state.soumission_data.get('taux', {
            'admin': 0.03,
            'contingency': 0.12,
            'profit': 0.15
        })
        
        admin_amount = total_travaux * taux['admin']
        contingency_amount = total_travaux * taux['contingency']
        profit_amount = total_travaux * taux['profit']
        
        sous_total = total_travaux + admin_amount + contingency_amount + profit_amount
        
        tps = sous_total * 0.05
        tvq = sous_total * 0.09975
        
        total_final = sous_total + tps + tvq
        
        # Sauvegarder les totaux
        st.session_state.soumission_data['totaux'] = {
            'travaux': total_travaux,
            'administration': admin_amount,
            'contingences': contingency_amount,
            'profit': profit_amount,
            'sous_total': sous_total,
            'tps': tps,
            'tvq': tvq,
            'total': total_final
        }
        
        # Style pour le tableau récapitulatif
        st.markdown("""
        <style>
            .recap-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            .recap-table td {
                padding: 10px;
                border-bottom: 1px solid #e5e7eb;
            }
            .recap-table .label {
                font-weight: 600;
                color: #4b5563;
            }
            .recap-table .value {
                text-align: right;
                font-weight: 500;
            }
            .recap-table .category-row {
                background: #f9fafb;
            }
            .recap-table .subtotal-row {
                background: #FAFBFF;
                font-weight: bold;
            }
            .recap-table .total-row {
                background: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
                color: white;
                font-size: 1.2em;
                font-weight: bold;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Affichage du récapitulatif avec colonnes Streamlit
        st.markdown("#### Détail par catégorie")
        
        # Récap par catégorie
        for cat_id, category in CATEGORIES.items():
            cat_total = sum(
                item.get('montant', 0) 
                for key, item in st.session_state.soumission_data['items'].items()
                if key.startswith(cat_id + "_")
            )
            if cat_total > 0:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{category['name']}**")
                with col2:
                    st.write(f"**${cat_total:,.2f}**")
        
        st.markdown("---")
        st.markdown("#### Calcul du total")
        
        # Total des travaux
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Total des travaux**")
        with col2:
            st.markdown(f"**${total_travaux:,.2f}**")
        
        # Frais supplémentaires
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Administration ({taux['admin']*100:.0f}%)")
        with col2:
            st.write(f"${admin_amount:,.2f}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Contingences ({taux['contingency']*100:.0f}%)")
        with col2:
            st.write(f"${contingency_amount:,.2f}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Profit ({taux['profit']*100:.0f}%)")
        with col2:
            st.write(f"${profit_amount:,.2f}")
        
        st.markdown("---")
        
        # Sous-total avant taxes
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Sous-total avant taxes**")
        with col2:
            st.markdown(f"**${sous_total:,.2f}**")
        
        # Taxes
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("TPS (5%)")
        with col2:
            st.write(f"${tps:,.2f}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("TVQ (9.975%)")
        with col2:
            st.write(f"${tvq:,.2f}")
        
        st.markdown("---")
        
        # Total final avec style
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;">
            <span style="font-size: 1.5em; font-weight: bold;">TOTAL FINAL</span>
            <span style="font-size: 1.8em; font-weight: bold;">${total_final:,.2f}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Graphique de répartition
        if total_travaux > 0:
            try:
                import plotly.graph_objects as go
                
                st.markdown("### 📈 Répartition des coûts")
                
                # Données pour le graphique
                labels = []
                values = []
                
                for cat_id, category in CATEGORIES.items():
                    cat_total = sum(
                        item.get('montant', 0) 
                        for key, item in st.session_state.soumission_data['items'].items()
                        if key.startswith(cat_id + "_")
                    )
                    if cat_total > 0:
                        labels.append(category['name'].split(' - ')[1])
                        values.append(cat_total)
                
                # Créer le graphique en secteurs
                fig = go.Figure(data=[go.Pie(
                    labels=labels, 
                    values=values,
                    hole=.3,
                    marker=dict(colors=['#3B82F6', '#2563EB', '#1F2937', '#d1d5db', '#E5E7EB', '#f3f4f6', '#FAFBFF', '#1D4ED8'])
                )])
                
                fig.update_layout(
                    height=400,
                    showlegend=True,
                    font=dict(size=12)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except ImportError:
                # Si plotly n'est pas installé, afficher une version texte
                st.markdown("### 📈 Répartition des coûts")
                st.info("📊 Graphique non disponible (plotly non installé)")
                
                # Afficher les pourcentages en texte
                for cat_id, category in CATEGORIES.items():
                    cat_total = sum(
                        item.get('montant', 0) 
                        for key, item in st.session_state.soumission_data['items'].items()
                        if key.startswith(cat_id + "_")
                    )
                    if cat_total > 0:
                        percentage = (cat_total / total_travaux) * 100
                        st.write(f"**{category['name'].split(' - ')[1]}**: ${cat_total:,.2f} ({percentage:.1f}%)")
        
        # Conditions et exclusions
        st.markdown("### 📝 Conditions")
        conditions = st.text_area(
            "Conditions de la soumission",
            value="• Cette soumission est valide pour 30 jours\n• Prix sujet à changement selon les conditions du site\n• 50% d'acompte requis à la signature du contrat",
            height=100
        )
        st.session_state.soumission_data['conditions'] = conditions.split('\n')
        
        st.markdown("### ⚠️ Exclusions")
        exclusions = st.text_area(
            "Exclusions de la soumission",
            value="• Décontamination (si applicable)\n• Mobilier et électroménagers\n• Aménagement paysager (sauf si spécifié)",
            height=100
        )
        st.session_state.soumission_data['exclusions'] = exclusions.split('\n')
    
    with tab4:
        st.markdown("### 💾 Actions sur la soumission")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Sauvegarder", type="primary"):
                if save_soumission():
                    st.success("✅ Soumission sauvegardée avec succès!")
                    st.balloons()
                else:
                    st.error("❌ Erreur lors de la sauvegarde")
        
        with col2:
            if st.button("📄 Générer PDF"):
                with st.spinner("Génération du document en cours..."):
                    file_path = generate_pdf()
                    if file_path:
                        # Lire le fichier généré
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                        
                        # Déterminer le type de fichier et le MIME type
                        if file_path.endswith('.pdf'):
                            mime_type = "application/pdf"
                            file_ext = ".pdf"
                        else:
                            # C'est un HTML
                            mime_type = "text/html"
                            file_ext = ".html"
                        
                        # Bouton de téléchargement
                        st.download_button(
                            label="📥 Télécharger le document",
                            data=file_content,
                            file_name=f"soumission_{st.session_state.soumission_data['numero']}{file_ext}",
                            mime=mime_type,
                            help="Cliquez pour télécharger la soumission"
                        )
                        
                        if file_ext == ".html":
                            st.info("""
                            💡 **Document HTML généré avec succès!**
                            
                            Pour créer un PDF :
                            1. Cliquez sur "📥 Télécharger le document"
                            2. Ouvrez le fichier HTML dans votre navigateur
                            3. Appuyez sur Ctrl+P (ou Cmd+P sur Mac)
                            4. Choisissez "Enregistrer en PDF" comme imprimante
                            5. Cliquez sur "Enregistrer"
                            
                            Le document est déjà formaté pour une impression parfaite!
                            """)
                        
                        # Nettoyer le fichier temporaire
                        try:
                            os.remove(file_path)
                        except:
                            pass
        
        with col3:
            if st.button("🔄 Nouvelle soumission"):
                st.session_state.soumission_data = {
                    'numero': generate_numero_soumission(),
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'client': {},
                    'projet': {},
                    'items': {},
                    'totaux': {},
                    'conditions': [],
                    'exclusions': []
                }
                st.rerun()
        
        # Afficher les informations de la soumission
        st.markdown("### 📋 Informations de la soumission")
        st.info(f"""
        **Numéro:** {st.session_state.soumission_data['numero']}  
        **Date:** {st.session_state.soumission_data['date']}  
        **Client:** {st.session_state.soumission_data['client'].get('nom', 'Non défini')}  
        **Projet:** {st.session_state.soumission_data['projet'].get('nom', 'Non défini')}  
        **Total:** ${st.session_state.soumission_data['totaux'].get('total', 0):,.2f}
        """)

def generate_numero_soumission():
    """Génère un numéro de soumission unique en utilisant le gestionnaire unifié"""
    try:
        from numero_manager import get_safe_unique_number
        return get_safe_unique_number()
    except ImportError:
        # Fallback amélioré qui vérifie TOUTES les bases de données
        year = datetime.now().year
        max_num = 0

        # Créer le dossier data s'il n'existe pas
        data_dir = os.getenv('DATA_DIR', 'data')
        os.makedirs(data_dir, exist_ok=True)

        # 1. Vérifier dans soumissions_heritage.db
        try:
            db_path = os.path.join(os.getenv('DATA_DIR', 'data'), 'soumissions_heritage.db')
            conn_heritage = sqlite3.connect(db_path)
            cursor_heritage = conn_heritage.cursor()
            cursor_heritage.execute('''
                CREATE TABLE IF NOT EXISTS soumissions_heritage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT UNIQUE,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor_heritage.execute('''
                SELECT numero FROM soumissions_heritage
                WHERE numero LIKE ?
                ORDER BY numero DESC LIMIT 1
            ''', (f'{year}-%',))
            heritage_result = cursor_heritage.fetchone()
            conn_heritage.close()

            if heritage_result and heritage_result[0]:
                try:
                    heritage_num = int(heritage_result[0].split('-')[1])
                    max_num = max(max_num, heritage_num)
                except:
                    pass
        except Exception as e:
            print(f"Erreur lecture heritage: {e}")

        # 2. Vérifier dans soumissions_multi.db
        try:
            multi_db_path = os.path.join(os.getenv('DATA_DIR', 'data'), 'soumissions_multi.db')
            if os.path.exists(multi_db_path):
                db_path = os.path.join(os.getenv('DATA_DIR', 'data'), 'soumissions_multi.db')
                conn_multi = sqlite3.connect(db_path)
                cursor_multi = conn_multi.cursor()
                cursor_multi.execute('''
                    SELECT numero_soumission FROM soumissions
                    WHERE numero_soumission LIKE ?
                    ORDER BY numero_soumission DESC LIMIT 1
                ''', (f'{year}-%',))
                multi_result = cursor_multi.fetchone()
                conn_multi.close()

                if multi_result and multi_result[0]:
                    try:
                        multi_num = int(multi_result[0].split('-')[1])
                        max_num = max(max_num, multi_num)
                    except:
                        pass
        except Exception as e:
            print(f"Erreur lecture multi: {e}")

        # 3. Vérifier aussi dans bon_commande.db au cas où
        try:
            bon_db_path = os.path.join(os.getenv('DATA_DIR', 'data'), 'bon_commande.db')
            if os.path.exists(bon_db_path):
                db_path = os.path.join(os.getenv('DATA_DIR', 'data'), 'bon_commande.db')
                conn_bon = sqlite3.connect(db_path)
                cursor_bon = conn_bon.cursor()
                # Vérifier si la table existe
                cursor_bon.execute('''
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='bons_commande'
                ''')
                if cursor_bon.fetchone():
                    cursor_bon.execute('''
                        SELECT numero_bon FROM bons_commande
                        WHERE numero_bon LIKE ? AND numero_bon NOT LIKE 'BC-%'
                        ORDER BY numero_bon DESC LIMIT 1
                    ''', (f'{year}-%',))
                    bon_result = cursor_bon.fetchone()
                    if bon_result and bon_result[0]:
                        try:
                            bon_num = int(bon_result[0].split('-')[1])
                            max_num = max(max_num, bon_num)
                        except:
                            pass
                conn_bon.close()
        except:
            pass

        # Retourner le prochain numéro disponible avec vérification d'unicité
        next_num = max_num + 1
        return f"{year}-{next_num:03d}"

def save_soumission():
    """Sauvegarde la soumission dans la base de données"""
    try:
        # Créer le dossier data s'il n'existe pas
        data_dir = os.getenv('DATA_DIR', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        db_path = os.path.join(os.getenv('DATA_DIR', 'data'), 'soumissions_heritage.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la table existe et obtenir sa structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='soumissions_heritage'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Vérifier les colonnes existantes
            cursor.execute("PRAGMA table_info(soumissions_heritage)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Si les colonnes nécessaires n'existent pas, recréer la table
            required_columns = ['numero', 'client_nom', 'projet_nom', 'montant_total', 'data', 'token', 'lien_public']
            if not all(col in columns for col in required_columns):
                # Sauvegarder les données existantes si possible
                try:
                    cursor.execute("SELECT * FROM soumissions_heritage")
                    old_data = cursor.fetchall()
                except:
                    old_data = []
                
                # Supprimer et recréer la table
                cursor.execute("DROP TABLE IF EXISTS soumissions_heritage")
                cursor.execute('''
                    CREATE TABLE soumissions_heritage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        numero TEXT UNIQUE,
                        client_nom TEXT,
                        projet_nom TEXT,
                        montant_total REAL,
                        data TEXT,
                        statut TEXT DEFAULT 'en_attente',
                        token TEXT UNIQUE,
                        lien_public TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
        else:
            # Créer la table si elle n'existe pas
            cursor.execute('''
                CREATE TABLE soumissions_heritage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT UNIQUE,
                    client_nom TEXT,
                    projet_nom TEXT,
                    montant_total REAL,
                    data TEXT,
                    statut TEXT DEFAULT 'en_attente',
                    token TEXT UNIQUE,
                    lien_public TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Préparer les données pour la sérialisation JSON
        # Copier les données pour éviter de modifier l'original
        data_to_save = st.session_state.soumission_data.copy()
        
        # Convertir les dates en string si elles existent
        if 'projet' in data_to_save and 'date_debut' in data_to_save['projet']:
            if hasattr(data_to_save['projet']['date_debut'], 'isoformat'):
                data_to_save['projet']['date_debut'] = data_to_save['projet']['date_debut'].isoformat()
        
        # Sauvegarder la soumission
        data_json = json.dumps(data_to_save, ensure_ascii=False, default=str)
        
        # Générer un token unique
        import uuid
        token = str(uuid.uuid4())
        
        # Déterminer l'URL de base selon l'environnement
        if os.getenv('APP_URL'):
            base_url = os.getenv('APP_URL')
        # Vérifier si on est sur Hugging Face Spaces
        elif os.getenv('SPACE_ID') or os.getenv('SPACE_HOST'):
            # Récupérer l'URL Hugging Face depuis les variables d'environnement
            space_host = os.getenv('SPACE_HOST')
            if space_host:
                base_url = f"https://{space_host}"
            else:
                # Fallback: construire l'URL depuis SPACE_ID
                space_id = os.getenv('SPACE_ID')
                if space_id:
                    base_url = f"https://huggingface.co/spaces/{space_id}"
                else:
                    # Si rien ne fonctionne, utiliser votre URL connue
                    base_url = 'https://huggingface.co/spaces/Sylvainleduc/C2B'
        elif os.getenv('RENDER'):
            base_url = 'https://c2b-heritage.onrender.com'
        else:
            base_url = 'http://localhost:8501'
        
        lien_public = f"{base_url}/?token={token}&type=heritage"
        
        cursor.execute('''
            INSERT OR REPLACE INTO soumissions_heritage 
            (numero, client_nom, projet_nom, montant_total, data, token, lien_public, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            st.session_state.soumission_data['numero'],
            st.session_state.soumission_data['client'].get('nom', ''),
            st.session_state.soumission_data['projet'].get('nom', ''),
            st.session_state.soumission_data['totaux'].get('total', 0),
            data_json,
            token,
            lien_public
        ))
        
        conn.commit()
        conn.close()

        # Ajouter automatiquement l'événement au calendrier
        try:
            from calendar_manager import add_event
            from datetime import datetime, timedelta

            # Créer un événement de suivi dans 7 jours
            date_suivi = datetime.now() + timedelta(days=7)

            add_event(
                titre=f"Suivi soumission {st.session_state.soumission_data['numero']}",
                description=f"Suivi de la soumission pour {st.session_state.soumission_data['client'].get('nom', 'Client')} - Projet: {st.session_state.soumission_data['projet'].get('nom', 'N/A')}",
                date_debut=date_suivi,
                type_event='soumission',
                reference_id=st.session_state.soumission_data['numero'],
                client_nom=st.session_state.soumission_data['client'].get('nom', ''),
                statut='en_attente',
                couleur='#3B82F6'
            )
        except Exception as e:
            # Si erreur calendrier, ne pas bloquer la sauvegarde
            print(f"Erreur ajout calendrier: {e}")

        return True
    except Exception as e:
        st.error(f"Erreur: {str(e)}")
        return False

def generate_pdf():
    """Génère un PDF de la soumission"""
    try:
        # Générer le contenu HTML formaté
        html_content = generate_html_for_pdf()
        
        # Pour l'instant, on génère toujours un HTML
        # (pdfkit nécessite wkhtmltopdf qui doit être installé séparément)
        import tempfile
        html_file = tempfile.mktemp(suffix='.html')
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
        
    except Exception as e:
        st.error(f"Erreur lors de la génération du document : {str(e)}")
        return None

def generate_html_for_pdf():
    """Génère un HTML formaté pour conversion en PDF"""
    data = st.session_state.soumission_data
    
    # Récupérer les informations de l'entreprise
    company = get_company_info()
    
    # Calculer les totaux pour affichage
    total_travaux = sum(
        item.get('montant', 0) 
        for item in data['items'].values()
    )
    
    # Style CSS pour le PDF
    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Soumission """ + data['numero'] + """</title>
        <style>
            @page {
                size: letter;
                margin: 0.75in;
            }
            
            body {
                font-family: Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.4;
                color: #333;
                margin: 0;
                padding: 0;
            }
            
            .header {
                text-align: center;
                border-bottom: 3px solid #3B82F6;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }

            .header h1 {
                color: #3B82F6;
                margin: 0;
                font-size: 24pt;
            }

            .header h2 {
                color: #2563EB;
                margin: 5px 0;
                font-size: 18pt;
            }
            
            .header p {
                margin: 5px 0;
                color: #666;
            }
            
            .info-section {
                margin-bottom: 25px;
                padding: 15px;
                background: #FAFBFF;
                border-left: 4px solid #3B82F6;
            }

            .info-section h3 {
                color: #3B82F6;
                margin: 0 0 10px 0;
                font-size: 14pt;
            }
            
            .info-section p {
                margin: 5px 0;
                font-size: 11pt;
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 25px;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                page-break-inside: avoid;
            }
            
            th {
                background: #3B82F6;
                color: white;
                padding: 10px;
                text-align: left;
                font-size: 11pt;
            }

            td {
                padding: 8px 10px;
                border-bottom: 1px solid #E5E7EB;
                font-size: 10pt;
            }

            tr:nth-child(even) {
                background: #FAFBFF;
            }

            .category-header {
                background: #E5E7EB;
                font-weight: bold;
                font-size: 12pt;
            }
            
            .category-header td {
                padding: 12px 10px;
                border-bottom: 2px solid #9ca3af;
            }
            
            .text-right {
                text-align: right;
            }
            
            .text-center {
                text-align: center;
            }
            
            .total-section {
                margin-top: 30px;
                padding: 20px;
                background: #FAFBFF;
                border: 2px solid #3B82F6;
                page-break-inside: avoid;
            }
            
            .total-row {
                display: flex;
                justify-content: space-between;
                padding: 5px 0;
                font-size: 11pt;
            }
            
            .total-row.final {
                font-size: 16pt;
                font-weight: bold;
                color: #3B82F6;
                border-top: 2px solid #3B82F6;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            .conditions {
                margin-top: 30px;
                padding: 15px;
                background: #fef3c7;
                border: 1px solid #f59e0b;
            }
            
            .conditions h4 {
                color: #d97706;
                margin: 0 0 10px 0;
            }
            
            .conditions ul {
                margin: 5px 0 5px 20px;
                padding: 0;
            }
            
            .footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #3B82F6;
                text-align: center;
                font-size: 9pt;
                color: #666;
            }
            
            .company-info {
                margin-top: 20px;
                padding: 10px;
                background: #f9fafb;
                font-size: 9pt;
            }
            
            @media print {
                .page-break {
                    page-break-before: always;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SOUMISSION BUDGÉTAIRE</h1>
            <h2>""" + company['name'] + """</h2>
            <p>Numéro: """ + data['numero'] + """ | Date: """ + data['date'] + """</p>
        </div>
        
        <div class="info-grid">
            <div class="info-section">
                <h3>👤 Informations Client</h3>
                <p><strong>Nom:</strong> """ + data['client'].get('nom', 'N/A') + """</p>
                <p><strong>Adresse:</strong> """ + data['client'].get('adresse', 'N/A') + """</p>
                <p><strong>Ville:</strong> """ + data['client'].get('ville', 'N/A') + """ """ + data['client'].get('code_postal', '') + """</p>
                <p><strong>Téléphone:</strong> """ + data['client'].get('telephone', 'N/A') + """</p>
                <p><strong>Courriel:</strong> """ + data['client'].get('courriel', 'N/A') + """</p>
            </div>
            
            <div class="info-section">
                <h3>🏗️ Informations Projet</h3>
                <p><strong>Nom du projet:</strong> """ + data['projet'].get('nom', 'N/A') + """</p>
                <p><strong>Adresse:</strong> """ + data['projet'].get('adresse', 'N/A') + """</p>
                <p><strong>Type:</strong> """ + str(data['projet'].get('type', 'N/A')) + """</p>
                <p><strong>Superficie:</strong> """ + str(data['projet'].get('superficie', 0)) + """ pi²</p>
                <p><strong>Étages:</strong> """ + str(data['projet'].get('etages', 1)) + """</p>
                <p><strong>Début prévu:</strong> """ + str(data['projet'].get('date_debut', 'N/A')) + """</p>
                <p><strong>Durée estimée:</strong> """ + data['projet'].get('duree', 'N/A') + """</p>
            </div>
        </div>
        
        <h3 style="color: #3B82F6; margin-top: 30px;">Détails des travaux</h3>
        <table>
            <thead>
                <tr>
                    <th style="width: 50%;">Description</th>
                    <th style="width: 10%;" class="text-center">Quantité</th>
                    <th style="width: 20%;" class="text-right">Coût unitaire</th>
                    <th style="width: 20%;" class="text-right">Total</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Ajouter les items par catégorie
    for cat_id, category in CATEGORIES.items():
        cat_total = sum(
            item.get('montant', 0) 
            for key, item in data['items'].items()
            if key.startswith(cat_id + "_")
        )
        
        if cat_total > 0:
            html += f"""
                <tr class="category-header">
                    <td colspan="4">{category['name']}</td>
                </tr>
            """
            
            for key, item in data['items'].items():
                if key.startswith(cat_id + "_") and item.get('montant', 0) > 0:
                    # S'assurer que les champs existent
                    titre = item.get('titre', 'Item')
                    description = item.get('description', '')
                    quantite = item.get('quantite', 1)
                    prix_unitaire = item.get('prix_unitaire', 0)
                    montant = item.get('montant', 0)
                    
                    html += f"""
                    <tr>
                        <td>
                            <strong>{titre}</strong><br>
                            <small style="color: #666;">{description}</small>
                        </td>
                        <td class="text-center">{quantite:.1f}</td>
                        <td class="text-right">${prix_unitaire:,.2f}</td>
                        <td class="text-right"><strong>${montant:,.2f}</strong></td>
                    </tr>
                    """
            
            html += f"""
                <tr style="background: #E5E7EB;">
                    <td colspan="3" class="text-right"><strong>Sous-total {category['name'].split(' - ')[1]}:</strong></td>
                    <td class="text-right"><strong>${cat_total:,.2f}</strong></td>
                </tr>
            """
    
    # Section des totaux
    html += f"""
            </tbody>
        </table>
        
        <div class="total-section">
            <h3 style="color: #3B82F6; margin: 0 0 15px 0;">Récapitulatif financier</h3>
            <div class="total-row">
                <span>Total des travaux:</span>
                <span>${data['totaux'].get('travaux', 0):,.2f}</span>
            </div>
            <div class="total-row">
                <span>Administration ({data['taux'].get('admin', 0.03)*100:.0f}%):</span>
                <span>${data['totaux'].get('administration', 0):,.2f}</span>
            </div>
            <div class="total-row">
                <span>Contingences ({data['taux'].get('contingency', 0.12)*100:.0f}%):</span>
                <span>${data['totaux'].get('contingences', 0):,.2f}</span>
            </div>
            <div class="total-row">
                <span>Profit ({data['taux'].get('profit', 0.15)*100:.0f}%):</span>
                <span>${data['totaux'].get('profit', 0):,.2f}</span>
            </div>
            <hr style="margin: 10px 0;">
            <div class="total-row">
                <span><strong>Sous-total avant taxes:</strong></span>
                <span><strong>${data['totaux'].get('sous_total', 0):,.2f}</strong></span>
            </div>
            <div class="total-row">
                <span>TPS (5%):</span>
                <span>${data['totaux'].get('tps', 0):,.2f}</span>
            </div>
            <div class="total-row">
                <span>TVQ (9.975%):</span>
                <span>${data['totaux'].get('tvq', 0):,.2f}</span>
            </div>
            <div class="total-row final">
                <span>TOTAL FINAL:</span>
                <span>${data['totaux'].get('total', 0):,.2f}</span>
            </div>
        </div>
    """
    
    # Conditions et exclusions
    if data.get('conditions'):
        html += """
        <div class="conditions">
            <h4>📝 Conditions</h4>
            <ul>
        """
        for condition in data['conditions']:
            if condition.strip():
                html += f"<li>{condition}</li>"
        html += "</ul></div>"
    
    if data.get('exclusions'):
        html += """
        <div class="conditions" style="background: #fee2e2; border-color: #ef4444;">
            <h4 style="color: #dc2626;">⚠️ Exclusions</h4>
            <ul>
        """
        for exclusion in data['exclusions']:
            if exclusion.strip():
                html += f"<li>{exclusion}</li>"
        html += "</ul></div>"
    
    # Footer avec informations de l'entreprise
    html += f"""
        <div class="footer">
            <div class="company-info">
                <strong>""" + company['name'] + """</strong><br>
                """ + company['address'] + """, """ + company['city'] + """<br>
                Tél: """ + company['phone'] + """<br>
                """ + company['email'] + """<br>
                RBQ: """ + company['rbq'] + """ | NEQ: """ + company['neq'] + """
            </div>
            <p style="margin-top: 20px;">
                Cette soumission est valide pour 30 jours à partir de la date d'émission.<br>
                Merci de votre confiance!
            </p>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_html():
    """Génère le HTML de la soumission avec le style magnifique du template"""
    data = st.session_state.soumission_data
    
    # Récupérer les informations de l'entreprise
    company = get_company_info()
    
    # Récupérer les paramètres commerciaux
    if DYNAMIC_CONFIG:
        params = get_commercial_params()
        taux = data.get('taux', {
            'admin': params['taux_administration'] / 100,
            'contingency': params['taux_contingences'] / 100,
            'profit': params['taux_profit'] / 100
        })
        colors = get_company_colors()
        logo = get_company_logo()
    else:
        taux = data.get('taux', {
            'admin': 0.03,
            'contingency': 0.12,
            'profit': 0.15
        })
        colors = {
            'primary': '#3B82F6',
            'secondary': '#2563EB',
            'accent': '#1F2937'
        }
        logo = ''
    
    # Calculer les totaux
    total_travaux = sum(
        item.get('montant', 0) 
        for item in data.get('items', {}).values()
    )
    
    admin_amount = total_travaux * taux['admin']
    contingency_amount = total_travaux * taux['contingency']
    profit_amount = total_travaux * taux['profit']
    
    sous_total = total_travaux + admin_amount + contingency_amount + profit_amount
    
    tps = sous_total * 0.05
    tvq = sous_total * 0.09975
    
    total_final = sous_total + tps + tvq
    
    # HTML avec le style magnifique du template
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soumission {data.get('numero', '')} - {company['name']}</title>
    <style>
        /* Variables CSS */
        :root {{
            --primary-color: {colors['primary']};
            --primary-light: {colors['secondary']};
            --primary-dark: {colors['accent']};
            --primary-bg: #FAFBFF;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            --transition-base: all 0.3s ease;
        }}

        /* Reset et Base */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
            line-height: 1.3;
            color: #333;
            background: #f5f5f5;
            min-height: 100vh;
        }}

        /* Conteneur principal */
        .container {{
            max-width: 8.5in;
            margin: 20px auto;
            background: white;
            box-shadow: var(--shadow-lg);
            padding: 0.4in;
            position: relative;
        }}

        @media print {{
            body {{ background: white; }}
            .container {{
                margin: 0;
                box-shadow: none;
                padding: 0.3in;
                max-width: 100%;
            }}
            .no-print {{ display: none !important; }}
            .page-break {{ page-break-before: always; }}
        }}

        /* Header avec gradient */
        .header-gradient {{
            background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-color) 100%);
            color: white;
            padding: 30px;
            margin: -0.4in -0.4in 20px -0.4in;
            text-align: center;
            box-shadow: var(--shadow-md);
        }}

        .header-gradient h1 {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 10px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}

        .header-gradient h2 {{
            font-size: 16px;
            font-weight: 400;
            opacity: 0.95;
            margin-bottom: 5px;
        }}

        .header-gradient .numero {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 10px;
            font-weight: 500;
        }}

        /* Informations entreprise */
        .company-header {{
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 15px;
            margin-bottom: 20px;
            text-align: right;
        }}

        .company-info {{
            font-size: 10px;
            line-height: 1.4;
            color: #555;
        }}

        .company-info strong {{
            color: var(--primary-dark);
            font-size: 12px;
        }}

        /* Boîtes d'information */
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 25px;
        }}

        .info-box {{
            background: var(--primary-bg);
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid var(--primary-color);
            box-shadow: var(--shadow-sm);
        }}

        .info-box h3 {{
            color: var(--primary-dark);
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .info-box p {{
            font-size: 10px;
            line-height: 1.4;
            color: #444;
            margin: 3px 0;
        }}

        .info-box p strong {{
            color: var(--primary-dark);
            font-weight: 600;
        }}

        /* Tableau principal */
        .table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 20px 0;
            box-shadow: var(--shadow-sm);
            border-radius: 8px;
            overflow: hidden;
        }}

        .table-header {{
            background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-color) 100%);
            color: white;
        }}

        .table-header th {{
            padding: 10px 8px;
            font-size: 10px;
            font-weight: 600;
            text-align: left;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: none;
        }}

        .table-header th:nth-child(1) {{ width: 50%; }}
        .table-header th:nth-child(2) {{ width: 12%; text-align: center; }}
        .table-header th:nth-child(3) {{ width: 19%; text-align: right; }}
        .table-header th:nth-child(4) {{ width: 19%; text-align: right; }}

        .table td {{
            padding: 6px 8px;
            font-size: 10px;
            border-bottom: 1px solid #e5e7eb;
            vertical-align: top;
        }}

        .table tr:hover {{
            background: rgba(75, 85, 99, 0.02);
        }}

        /* Styles de lignes spéciales */
        .category-header-row td {{
            background: var(--primary-bg);
            font-weight: bold;
            padding: 8px !important;
            color: var(--primary-dark);
            font-size: 11px;
            border-top: 1px solid #d1d5db;
            border-bottom: 1px solid #d1d5db;
        }}

        .subtotal-row td {{
            background: #f3f4f6;
            font-weight: bold;
            padding: 8px !important;
            color: var(--primary-color);
            border-top: 1px solid #e5e7eb;
        }}

        .total-row td {{
            background: var(--primary-bg);
            font-weight: bold;
            font-size: 11px;
            padding: 10px 8px;
            border-top: 2px solid var(--primary-color);
        }}

        .grand-total-row td {{
            background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-color) 100%);
            color: white;
            font-weight: bold;
            font-size: 13px;
            padding: 12px 8px;
            border: none;
        }}

        /* Descriptions d'items */
        .item-title {{
            font-weight: 600;
            color: #222;
            font-size: 10px;
            margin-bottom: 2px;
        }}

        .item-description {{
            font-size: 9px;
            color: #666;
            font-style: italic;
            line-height: 1.3;
            margin-top: 2px;
        }}

        /* Alignements */
        .text-center {{ text-align: center; }}
        .text-right {{ text-align: right; }}
        .text-left {{ text-align: left; }}

        /* Pied de page */
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid var(--primary-color);
            text-align: center;
        }}

        .footer-info {{
            background: var(--primary-bg);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}

        .footer-info p {{
            font-size: 10px;
            color: #555;
            margin: 5px 0;
        }}

        /* Conditions et exclusions */
        .conditions-box {{
            background: #fef5e7;
            border: 1px solid #f39c12;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }}

        .conditions-box h4 {{
            color: #e67e22;
            font-size: 12px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}

        .conditions-box ul {{
            margin: 5px 0 5px 20px;
            padding: 0;
        }}

        .conditions-box li {{
            font-size: 10px;
            color: #7f6000;
            margin: 3px 0;
        }}

        .exclusions-box {{
            background: #fee2e2;
            border: 1px solid #ef4444;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }}

        .exclusions-box h4 {{
            color: #dc2626;
            font-size: 12px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}

        .exclusions-box ul {{
            margin: 5px 0 5px 20px;
            padding: 0;
        }}

        .exclusions-box li {{
            font-size: 10px;
            color: #7f1d1d;
            margin: 3px 0;
        }}

        /* Badge de validité */
        .validity-badge {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            display: inline-block;
            font-size: 11px;
            font-weight: 600;
            margin: 10px 0;
            box-shadow: var(--shadow-md);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header avec gradient -->
        <div class="header-gradient">
            <h1>SOUMISSION BUDGÉTAIRE</h1>
            <h2>{company['name']}</h2>
            <div class="numero">№ {data.get('numero', '')} | {data.get('date', '')}</div>
        </div>

        <!-- Informations entreprise -->
        <div class="company-header">
            {f'<img src="{logo}" style="max-height: 80px; margin-bottom: 10px;">' if logo else ''}
            <div class="company-info">
                <strong>{company['name'].upper()}</strong><br>
                {company['address']}<br>
                {company['city']}<br>
                Tél: {company['phone']}{f' | Cell: {company["cell"]}' if company.get('cell') else ''}<br>
                {company['email']}<br>
                <small>RBQ: {company['rbq']} | NEQ: {company['neq']}</small>
            </div>
        </div>

        <!-- Grille d'informations -->
        <div class="info-grid">
            <div class="info-box">
                <h3>👤 Informations Client</h3>
                <p><strong>Nom:</strong> {data.get('client', {}).get('nom', 'N/A')}</p>
                <p><strong>Adresse:</strong> {data.get('client', {}).get('adresse', 'N/A')}</p>
                <p><strong>Ville:</strong> {data.get('client', {}).get('ville', 'N/A')} {data.get('client', {}).get('code_postal', '')}</p>
                <p><strong>Téléphone:</strong> {data.get('client', {}).get('telephone', 'N/A')}</p>
                <p><strong>Courriel:</strong> {data.get('client', {}).get('email', 'N/A')}</p>
            </div>

            <div class="info-box">
                <h3>🏗️ Informations Projet</h3>
                <p><strong>Nom:</strong> {data.get('projet', {}).get('nom', 'N/A')}</p>
                <p><strong>Adresse:</strong> {data.get('projet', {}).get('adresse', 'N/A')}</p>
                <p><strong>Type:</strong> {data.get('projet', {}).get('type', 'N/A')}</p>
                <p><strong>Superficie:</strong> {data.get('projet', {}).get('superficie', 0)} pi²</p>
                <p><strong>Début prévu:</strong> {data.get('projet', {}).get('date_debut', 'N/A')}</p>
                <p><strong>Durée:</strong> {data.get('projet', {}).get('duree', 'N/A')}</p>
            </div>
        </div>

        <!-- Tableau des travaux -->
        <table class="table">
            <thead class="table-header">
                <tr>
                    <th>Description des travaux</th>
                    <th class="text-center">Quantité</th>
                    <th class="text-right">Prix unitaire</th>
                    <th class="text-right">Montant</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Ajouter les items par catégorie
    for cat_id, category in CATEGORIES.items():
        cat_total = sum(
            item.get('montant', 0) 
            for key, item in data.get('items', {}).items()
            if key.startswith(cat_id + "_")
        )
        
        if cat_total > 0:
            html += f"""
                <tr class="category-header-row">
                    <td colspan="4">{category['name']}</td>
                </tr>
            """
            
            # Items de la catégorie
            for key, item in data.get('items', {}).items():
                if key.startswith(cat_id + "_") and item.get('montant', 0) > 0:
                    titre = item.get('titre', 'Item')
                    description = item.get('description', '')
                    quantite = item.get('quantite', 1)
                    prix_unitaire = item.get('prix_unitaire', 0)
                    montant = item.get('montant', 0)
                    
                    html += f"""
                    <tr>
                        <td>
                            <div class="item-title">{titre}</div>
                            <div class="item-description">{description}</div>
                        </td>
                        <td class="text-center">{quantite:.1f}</td>
                        <td class="text-right">${prix_unitaire:,.2f}</td>
                        <td class="text-right"><strong>${montant:,.2f}</strong></td>
                    </tr>
                    """
            
            # Sous-total de catégorie
            html += f"""
                <tr class="subtotal-row">
                    <td colspan="3" class="text-right">Sous-total {category['name'].split(' - ')[1]}</td>
                    <td class="text-right">${cat_total:,.2f}</td>
                </tr>
            """
    
    # Section des totaux
    html += f"""
                <tr class="total-row">
                    <td colspan="3" class="text-right">Total des travaux</td>
                    <td class="text-right">${total_travaux:,.2f}</td>
                </tr>
                <tr>
                    <td colspan="3" class="text-right">Administration ({taux.get('admin', 0.03)*100:.0f}%)</td>
                    <td class="text-right">${admin_amount:,.2f}</td>
                </tr>
                <tr>
                    <td colspan="3" class="text-right">Contingences ({taux.get('contingency', 0.12)*100:.0f}%)</td>
                    <td class="text-right">${contingency_amount:,.2f}</td>
                </tr>
                <tr>
                    <td colspan="3" class="text-right">Profit ({taux.get('profit', 0.15)*100:.0f}%)</td>
                    <td class="text-right">${profit_amount:,.2f}</td>
                </tr>
                <tr class="subtotal-row">
                    <td colspan="3" class="text-right"><strong>Sous-total avant taxes</strong></td>
                    <td class="text-right"><strong>${sous_total:,.2f}</strong></td>
                </tr>
                <tr>
                    <td colspan="3" class="text-right">TPS (5%)</td>
                    <td class="text-right">${tps:,.2f}</td>
                </tr>
                <tr>
                    <td colspan="3" class="text-right">TVQ (9.975%)</td>
                    <td class="text-right">${tvq:,.2f}</td>
                </tr>
                <tr class="grand-total-row">
                    <td colspan="3" class="text-right">MONTANT TOTAL</td>
                    <td class="text-right">${total_final:,.2f}</td>
                </tr>
            </tbody>
        </table>
    """
    
    # Conditions et exclusions
    conditions = data.get('conditions', [])
    exclusions = data.get('exclusions', [])
    
    # Gérer les conditions (peut être une liste ou un string)
    if conditions:
        if isinstance(conditions, list):
            # Si c'est une liste, joindre les éléments
            conditions_text = '\n'.join([str(c) for c in conditions if c])
        else:
            # Si c'est déjà un string
            conditions_text = str(conditions)
        
        if conditions_text.strip():
            html += """
            <div class="conditions-box">
                <h4>📝 Conditions</h4>
                <p style="font-size: 10px; color: #7f6000; margin: 5px 0;">
            """
            html += conditions_text.replace('\n', '<br>')
            html += """
                </p>
            </div>
            """
    
    # Gérer les exclusions (peut être une liste ou un string)
    if exclusions:
        if isinstance(exclusions, list):
            # Si c'est une liste, joindre les éléments
            exclusions_text = '\n'.join([str(e) for e in exclusions if e])
        else:
            # Si c'est déjà un string
            exclusions_text = str(exclusions)
        
        if exclusions_text.strip():
            html += """
            <div class="exclusions-box">
                <h4>⚠️ Exclusions</h4>
                <p style="font-size: 10px; color: #7f1d1d; margin: 5px 0;">
            """
            html += exclusions_text.replace('\n', '<br>')
            html += """
                </p>
            </div>
            """
    
    # Badge de validité
    html += """
        <div style="text-align: center; margin: 30px 0;">
            <div class="validity-badge">
                ✓ Cette soumission est valide pour 30 jours
            </div>
        </div>
    """
    
    # Pied de page
    html += f"""
        <div class="footer">
            <div class="footer-info">
                <p><strong>{company['name']}</strong></p>
                <p>{company['address']}, {company['city']}</p>
                <p>Tél: {company['phone']} | {company['email']}</p>
                <p>RBQ: {company['rbq']} | NEQ: {company['neq']} | TPS: {company['tps']} | TVQ: {company['tvq']}</p>
            </div>
            <p style="font-size: 10px; color: #999; margin-top: 20px;">
                Généré le {data.get('date', '')} | Soumission № {data.get('numero', '')}
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    return html
    

def show_soumission_heritage():
    """Fonction principale pour afficher le module de soumission"""
    create_soumission_form()

def get_saved_submission_html(submission_id):
    """Récupère le HTML d'une soumission sauvegardée"""
    try:
        db_path = os.path.join(os.getenv('DATA_DIR', 'data'), 'soumissions_heritage.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data FROM soumissions_heritage 
            WHERE id = ?
        ''', (submission_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            # Charger les données dans session state temporairement
            import streamlit as st
            data = json.loads(result[0])
            
            # S'assurer que soumission_data existe dans session_state
            if 'soumission_data' not in st.session_state:
                st.session_state.soumission_data = {
                    'items': {},
                    'client': {},
                    'projet': {},
                    'totaux': {},
                    'conditions': [],
                    'exclusions': []
                }

            # Restaurer les données dans session_state (en gardant la structure)
            st.session_state.soumission_data = data
            # S'assurer que 'items' existe après restauration
            if 'items' not in st.session_state.soumission_data:
                st.session_state.soumission_data['items'] = {}
            for key, value in data.items():
                st.session_state[key] = value
            
            # Générer le HTML avec les données restaurées
            return generate_html()
        return None
        
    except Exception as e:
        print(f"Erreur récupération soumission: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    company_name = get_company_info()['name']
    st.set_page_config(
        page_title=f"Soumission - {company_name}",
        page_icon="🏗️",
        layout="wide"
    )
    show_soumission_heritage()