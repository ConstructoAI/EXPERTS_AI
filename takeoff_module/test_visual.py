"""
Test visuel de la base de données Takeoff AI
Affiche le contenu de la base de données de manière formatée
"""
# -*- coding: utf-8 -*-
import sys
import io

# Forcer l'encodage UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from takeoff_db import get_all_projects, load_project, get_project_stats

def afficher_base():
    """Affiche le contenu complet de la base de données"""

    print("\n" + "=" * 70)
    print("📊 CONTENU DE LA BASE DE DONNÉES TAKEOFF AI")
    print("=" * 70)

    # Statistiques globales
    stats = get_project_stats()

    print("\n📈 STATISTIQUES GLOBALES")
    print("-" * 70)
    print(f"  📁 Total projets      : {stats['total_projects']}")
    print(f"  📏 Total mesures      : {stats['total_measurements']}")
    print(f"  💰 Montant total      : {stats['total_amount']:,.2f} $")
    print(f"  🟡 Projets en cours   : {stats['projects_en_cours']}")
    print(f"  🟢 Projets terminés   : {stats['projects_termines']}")

    # Liste des projets
    projects = get_all_projects()

    if not projects:
        print("\n⚠️  Aucun projet dans la base de données")
        return

    print(f"\n📂 LISTE DES PROJETS ({len(projects)})")
    print("-" * 70)

    for i, proj in enumerate(projects, 1):
        project_id, nom_projet, client_nom, pdf_nom, total_mesures, total_montant, date_creation, date_modification, statut = proj

        # Badge de statut
        statut_badges = {
            'en_cours': '🟡',
            'termine': '🟢',
            'archive': '⚪'
        }
        badge = statut_badges.get(statut, '🔵')

        print(f"\n{i}. {badge} {nom_projet}")
        print(f"   ID: {project_id}")
        if client_nom:
            print(f"   👤 Client: {client_nom}")
        if pdf_nom:
            print(f"   📄 PDF: {pdf_nom}")
        print(f"   📏 Mesures: {total_mesures}")
        print(f"   💰 Montant: {total_montant:,.2f} $")
        print(f"   📅 Créé: {date_creation}")
        print(f"   🔄 Modifié: {date_modification}")
        print(f"   🏷️  Statut: {statut}")

        # Charger les détails du projet
        data = load_project(project_id)
        if data and data['measurements']:
            print(f"\n   📋 Détail des mesures:")
            for j, mesure in enumerate(data['measurements'], 1):
                type_icons = {
                    'distance': '📏',
                    'surface': '📐',
                    'perimetre': '⭕',
                    'angle': '📐'
                }
                icon = type_icons.get(mesure['type'], '📊')

                produit = mesure.get('product', {})
                produit_nom = produit.get('name', 'N/D')
                produit_prix = produit.get('unit_price', 0)

                print(f"      {j}. {icon} {mesure['label']}")
                print(f"         Valeur: {mesure['value']:.2f} {mesure['unit']}")
                if produit_nom != 'N/D':
                    print(f"         Produit: {produit_nom}")
                    if produit_prix > 0:
                        cout_total = mesure['value'] * produit_prix
                        print(f"         Coût: {produit_prix:.2f} $/unité × {mesure['value']:.2f} = {cout_total:,.2f} $")

    print("\n" + "=" * 70)
    print("✅ Affichage terminé")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    afficher_base()
