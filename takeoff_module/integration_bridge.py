"""
Module pont d'intégration entre TAKEOFF AI et EXPERTS IA

Ce module convertit les mesures TAKEOFF en format compatible
avec le système de soumissions d'EXPERTS IA.
"""

import streamlit as st
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any


def export_to_soumission_experts(measurements: List[Dict],
                                 catalog: Any,
                                 pdf_name: str = None) -> Dict:
    """
    Exporte les mesures TAKEOFF vers une nouvelle soumission EXPERTS IA

    Args:
        measurements: Liste des mesures effectuées
        catalog: Instance du catalogue de produits
        pdf_name: Nom du fichier PDF source

    Returns:
        dict: Résultat de l'export avec succès/erreur
    """

    if not measurements:
        return {
            'success': False,
            'error': 'Aucune mesure à exporter'
        }

    try:
        # Convertir les mesures en items de soumission
        travaux = convert_measurements_to_soumission_items(measurements, catalog)

        # Calculer les totaux
        from entreprise_config import get_commercial_params

        try:
            params = get_commercial_params()
        except:
            # Valeurs par défaut si le module n'est pas accessible
            params = {
                'taux_administration': 3.0,
                'taux_contingences': 12.0,
                'taux_profit': 15.0
            }

        total_travaux = sum(t['sous_total'] for t in travaux)
        administration = total_travaux * (params['taux_administration'] / 100)
        contingences = total_travaux * (params['taux_contingences'] / 100)
        profit = total_travaux * (params['taux_profit'] / 100)
        total_avant_taxes = total_travaux + administration + contingences + profit
        tps = total_avant_taxes * 0.05
        tvq = total_avant_taxes * 0.09975
        investissement_total = total_avant_taxes + tps + tvq

        # Calculer la superficie totale
        superficie_totale = sum(
            m['value'] for m in measurements
            if m['type'] == 'surface' and 'pi' in m.get('unit', '')
        )

        # Préparer les données de soumission
        soumission_data = {
            'numero_soumission': f"TAKEOFF-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'date_soumission': datetime.now().strftime('%Y-%m-%d'),
            'source': 'TAKEOFF_AI',
            'pdf_source': pdf_name or 'Plan PDF',

            'client': {
                'nom': 'Client - Mesures TAKEOFF AI',
                'adresse': '',
                'ville': '',
                'province': 'Québec',
                'code_postal': ''
            },

            'projet': {
                'description': f"Projet basé sur mesures PDF: {pdf_name or 'plan.pdf'}",
                'type': 'Construction neuve',
                'superficie_pi2': round(superficie_totale, 2),
                'nb_etages': 1
            },

            'contact': {
                'nom': '',
                'telephone': '',
                'courriel': ''
            },

            'travaux': travaux,

            'recapitulatif': {
                'total_travaux': round(total_travaux, 2),
                'administration': round(administration, 2),
                'contingences': round(contingences, 2),
                'profit': round(profit, 2),
                'total_avant_taxes': round(total_avant_taxes, 2),
                'tps': round(tps, 2),
                'tvq': round(tvq, 2),
                'investissement_total': round(investissement_total, 2)
            }
        }

        # Stocker dans session state pour récupération dans l'onglet Soumissions
        st.session_state.pending_soumission_from_takeoff = soumission_data

        return {
            'success': True,
            'nb_items': sum(len(t['items']) for t in travaux),
            'nb_categories': len(travaux),
            'total_estime': investissement_total,
            'soumission_data': soumission_data
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def convert_measurements_to_soumission_items(measurements: List[Dict],
                                            catalog: Any) -> List[Dict]:
    """
    Convertit les mesures TAKEOFF en items de soumission EXPERTS IA

    Args:
        measurements: Liste des mesures
        catalog: Catalogue de produits

    Returns:
        List[Dict]: Liste des catégories de travaux avec leurs items
    """

    # Grouper par catégorie de produit
    items_by_category = defaultdict(list)

    # Mapping des catégories TAKEOFF vers catégories EXPERTS IA
    category_mapping = {
        'Béton': 'FONDATION ET STRUCTURE',
        'Acier d\'armature': 'FONDATION ET STRUCTURE',
        'Coffrages': 'FONDATION ET STRUCTURE',
        'Isolation': 'ISOLATION ET ÉTANCHÉITÉ',
        'Gypse': 'FINITIONS INTÉRIEURES',
        'Toiture': 'TOITURE',
        'Fenestration': 'CHARPENTE ET ENVELOPPE',
        'Portes et fenêtres': 'CHARPENTE ET ENVELOPPE',
        'Revêtement': 'REVÊTEMENTS EXTÉRIEURS',
        'Plomberie': 'PLOMBERIE',
        'Électricité': 'ÉLECTRICITÉ',
        'CVCA': 'SYSTÈMES MÉCANIQUES',
        'Ventilation': 'SYSTÈMES MÉCANIQUES',
    }

    for measure in measurements:
        product = measure.get('product', {})
        product_name = product.get('name', 'Item mesuré')
        product_category = product.get('category', 'Divers')

        # Mapper vers catégorie EXPERTS IA
        expert_category = category_mapping.get(product_category, 'AUTRES TRAVAUX')

        # Déterminer le ratio matériaux/main-d'œuvre selon la catégorie
        ratios = get_material_labor_ratio(expert_category)

        # Calculer les coûts
        quantite = measure.get('value', 0)
        prix_unitaire = product.get('price', 0)
        total = quantite * prix_unitaire

        materiaux_montant = total * (ratios['materiaux_pct'] / 100)
        main_oeuvre_montant = total * (ratios['main_oeuvre_pct'] / 100)

        # Créer l'item selon format EXPERTS IA
        item = {
            'description': product_name,
            'details': f"Mesuré sur plan PDF - {measure.get('label', 'Mesure TAKEOFF')}",
            'quantite': round(quantite, 2),
            'unite': measure.get('unit', 'pi²'),
            'materiaux': round(materiaux_montant, 2),
            'materiaux_pct': ratios['materiaux_pct'],
            'main_oeuvre': round(main_oeuvre_montant, 2),
            'main_oeuvre_pct': ratios['main_oeuvre_pct'],
            'total': round(total, 2),
            'prix_unitaire_global': round(prix_unitaire, 2),
            'source': 'TAKEOFF_AI',
            'type_mesure': measure.get('type', 'manual')
        }

        items_by_category[expert_category].append(item)

    # Construire la structure complète
    travaux = []

    for category, items in items_by_category.items():
        sous_total = sum(item['total'] for item in items)
        sous_total_materiaux = sum(item['materiaux'] for item in items)
        sous_total_main_oeuvre = sum(item['main_oeuvre'] for item in items)

        category_data = {
            'categorie': category,
            'items': items,
            'sous_total': round(sous_total, 2),
            'sous_total_materiaux': round(sous_total_materiaux, 2),
            'sous_total_main_oeuvre': round(sous_total_main_oeuvre, 2)
        }

        travaux.append(category_data)

    # Trier par catégorie pour cohérence
    travaux.sort(key=lambda x: x['categorie'])

    return travaux


def get_material_labor_ratio(category: str) -> Dict[str, int]:
    """
    Retourne les ratios matériaux/main-d'œuvre typiques par catégorie

    Args:
        category: Nom de la catégorie de travaux

    Returns:
        dict: Ratios en pourcentage
    """

    # Ratios basés sur les standards de l'industrie québécoise
    ratios = {
        'FONDATION ET STRUCTURE': {'materiaux_pct': 65, 'main_oeuvre_pct': 35},
        'CHARPENTE ET ENVELOPPE': {'materiaux_pct': 60, 'main_oeuvre_pct': 40},
        'TOITURE': {'materiaux_pct': 60, 'main_oeuvre_pct': 40},
        'REVÊTEMENTS EXTÉRIEURS': {'materiaux_pct': 55, 'main_oeuvre_pct': 45},
        'ISOLATION ET ÉTANCHÉITÉ': {'materiaux_pct': 55, 'main_oeuvre_pct': 45},
        'PLOMBERIE': {'materiaux_pct': 65, 'main_oeuvre_pct': 35},
        'ÉLECTRICITÉ': {'materiaux_pct': 60, 'main_oeuvre_pct': 40},
        'SYSTÈMES MÉCANIQUES': {'materiaux_pct': 60, 'main_oeuvre_pct': 40},
        'FINITIONS INTÉRIEURES': {'materiaux_pct': 40, 'main_oeuvre_pct': 60},
        'AUTRES TRAVAUX': {'materiaux_pct': 50, 'main_oeuvre_pct': 50},
    }

    return ratios.get(category, {'materiaux_pct': 50, 'main_oeuvre_pct': 50})


def get_pending_takeoff_soumission():
    """
    Récupère la soumission en attente depuis TAKEOFF AI

    Returns:
        dict ou None: Données de la soumission ou None si aucune
    """

    if 'pending_soumission_from_takeoff' in st.session_state:
        data = st.session_state.pending_soumission_from_takeoff
        # Effacer après récupération pour éviter les duplications
        del st.session_state.pending_soumission_from_takeoff
        return data

    return None


def has_pending_takeoff_soumission() -> bool:
    """
    Vérifie s'il y a une soumission TAKEOFF en attente

    Returns:
        bool: True si une soumission est en attente
    """

    return 'pending_soumission_from_takeoff' in st.session_state
