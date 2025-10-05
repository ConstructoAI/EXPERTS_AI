"""
Script de test pour la base de données Takeoff AI
Vérifie que toutes les fonctions fonctionnent correctement
"""
# -*- coding: utf-8 -*-
import sys
import io

# Forcer l'encodage UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from takeoff_db import (
    init_takeoff_db, save_project, save_measurement, save_all_measurements,
    get_all_projects, load_project, delete_project, get_project_stats,
    search_projects, update_project
)

def test_all():
    """Test complet de toutes les fonctions"""

    print("=" * 60)
    print("TEST DE LA BASE DE DONNÉES TAKEOFF AI")
    print("=" * 60)

    # 1. Initialisation
    print("\n1️⃣ Initialisation de la base de données...")
    try:
        init_takeoff_db()
        print("   ✅ Base de données initialisée")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return

    # 2. Création d'un projet
    print("\n2️⃣ Création d'un projet de test...")
    try:
        project_id = save_project(
            nom_projet="Projet Test - Maison Dupont",
            client_nom="M. Jean Dupont",
            pdf_nom="plan_test.pdf",
            calibration={'value': 1.5, 'unit': 'pi'},
            notes="Projet de test pour validation du système"
        )
        print(f"   ✅ Projet créé avec ID: {project_id}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return

    # 3. Ajout de mesures
    print("\n3️⃣ Ajout de mesures au projet...")
    try:
        mesures = [
            {
                'type': 'distance',
                'label': 'Mur extérieur Nord',
                'value': 25.5,
                'unit': 'pi',
                'page_number': 1,
                'points': [[0, 0], [25.5, 0]],
                'product': {
                    'name': 'Béton 25 MPa',
                    'category': 'Béton',
                    'unit_price': 150.0
                }
            },
            {
                'type': 'surface',
                'label': 'Surface dalle sous-sol',
                'value': 450.0,
                'unit': 'pi²',
                'page_number': 1,
                'points': [[0, 0], [30, 0], [30, 15], [0, 15]],
                'product': {
                    'name': 'Béton 30 MPa',
                    'category': 'Béton',
                    'unit_price': 165.0
                }
            },
            {
                'type': 'distance',
                'label': 'Périmètre fondation',
                'value': 90.0,
                'unit': 'pi',
                'page_number': 1,
                'points': [[0, 0], [30, 0], [30, 15], [0, 15], [0, 0]],
                'product': {
                    'name': 'Coffrage contreplaqué',
                    'category': 'Coffrages',
                    'unit_price': 12.0
                }
            }
        ]

        save_all_measurements(project_id, mesures)
        print(f"   ✅ {len(mesures)} mesures ajoutées")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return

    # 4. Récupération du projet
    print("\n4️⃣ Chargement du projet...")
    try:
        data = load_project(project_id)
        if data:
            projet = data['project']
            mesures_chargees = data['measurements']
            print(f"   ✅ Projet chargé: {projet['nom_projet']}")
            print(f"      - Client: {projet['client_nom']}")
            print(f"      - Mesures: {len(mesures_chargees)}")
            print(f"      - Montant total: {projet['total_montant']:.2f}$")
        else:
            print("   ❌ Projet non trouvé")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    # 5. Mise à jour du projet
    print("\n5️⃣ Mise à jour du projet...")
    try:
        update_project(
            project_id,
            notes="Notes mises à jour - Test validé!",
            statut="termine"
        )
        print("   ✅ Projet mis à jour")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    # 6. Création d'un second projet
    print("\n6️⃣ Création d'un second projet...")
    try:
        project_id_2 = save_project(
            nom_projet="Projet Test 2 - Rénovation",
            client_nom="Mme Marie Tremblay",
            pdf_nom="plan_renovation.pdf"
        )
        print(f"   ✅ Second projet créé avec ID: {project_id_2}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    # 7. Récupération de tous les projets
    print("\n7️⃣ Récupération de tous les projets...")
    try:
        projets = get_all_projects()
        print(f"   ✅ {len(projets)} projet(s) trouvé(s)")
        for i, proj in enumerate(projets, 1):
            print(f"      {i}. {proj[1]} - {proj[4]} mesures - {proj[5]:.2f}$ - {proj[8]}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    # 8. Recherche
    print("\n8️⃣ Test de recherche...")
    try:
        resultats = search_projects("Dupont")
        print(f"   ✅ Recherche 'Dupont': {len(resultats)} résultat(s)")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    # 9. Statistiques
    print("\n9️⃣ Statistiques globales...")
    try:
        stats = get_project_stats()
        print("   ✅ Statistiques:")
        print(f"      - Total projets: {stats['total_projects']}")
        print(f"      - Total mesures: {stats['total_measurements']}")
        print(f"      - Montant total: {stats['total_amount']:.2f}$")
        print(f"      - Projets en cours: {stats['projects_en_cours']}")
        print(f"      - Projets terminés: {stats['projects_termines']}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    # 10. Suppression du second projet (nettoyage)
    print("\n🔟 Nettoyage (suppression second projet)...")
    try:
        delete_project(project_id_2)
        print("   ✅ Second projet supprimé")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    # Résumé final
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)

    # Vérifier l'état final
    try:
        projets_finaux = get_all_projects()
        stats_finales = get_project_stats()

        print(f"\n✅ Tests terminés avec succès!")
        print(f"\nÉtat final:")
        print(f"  - Projets restants: {len(projets_finaux)}")
        print(f"  - Total mesures: {stats_finales['total_measurements']}")
        print(f"  - Montant total: {stats_finales['total_amount']:.2f}$")

        if len(projets_finaux) > 0:
            print(f"\n📊 Projet de test conservé:")
            print(f"  ID: {project_id}")
            print(f"  Nom: {projets_finaux[0][1]}")
            print(f"  Note: Vous pouvez le supprimer manuellement si désiré")
    except Exception as e:
        print(f"❌ Erreur lors du résumé: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_all()
