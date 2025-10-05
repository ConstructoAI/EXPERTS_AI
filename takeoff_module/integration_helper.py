"""
Script d'aide à l'intégration automatique de TAKEOFF AI dans EXPERTS IA

Ce script détecte automatiquement la structure de app.py et suggère
les modifications à effectuer.
"""

import re
import os


def analyze_app_structure(app_file_path):
    """Analyse la structure de app.py pour suggérer les modifications"""

    print("="*70)
    print("🔍 ANALYSE DE LA STRUCTURE DE APP.PY")
    print("="*70)

    if not os.path.exists(app_file_path):
        print(f"❌ Fichier non trouvé: {app_file_path}")
        return

    with open(app_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # Détecter les imports existants
    print("\n📦 IMPORTS DÉTECTÉS:")
    print("-" * 70)

    import_lines = []
    for i, line in enumerate(lines[:100], 1):  # Premiers 100 lignes
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            import_lines.append((i, line.strip()))

    for line_num, import_line in import_lines[-5:]:  # Afficher les 5 derniers
        print(f"  Ligne {line_num}: {import_line}")

    if import_lines:
        last_import_line = import_lines[-1][0]
        print(f"\n✅ Dernier import trouvé à la ligne {last_import_line}")
        print(f"\n💡 AJOUTEZ CES IMPORTS APRÈS LA LIGNE {last_import_line}:")
        print("-" * 70)
        print("""
# Import du module TAKEOFF AI
from takeoff_module import show_takeoff_interface
from takeoff_module.integration_bridge import (
    has_pending_takeoff_soumission,
    get_pending_takeoff_soumission
)
""")

    # Détecter la navigation/menu
    print("\n🗺️ NAVIGATION/MENU DÉTECTÉE:")
    print("-" * 70)

    navigation_patterns = [
        (r'st\.sidebar\.selectbox\(["\']([^"\']+)["\']', 'Sidebar selectbox'),
        (r'st\.sidebar\.radio\(["\']([^"\']+)["\']', 'Sidebar radio'),
        (r'st\.tabs\(\[', 'Tabs'),
        (r'if.*==.*["\']([^"\']+)["\']', 'Conditions if/elif'),
    ]

    navigation_found = []

    for i, line in enumerate(lines, 1):
        for pattern, nav_type in navigation_patterns:
            if re.search(pattern, line):
                navigation_found.append((i, nav_type, line.strip()))

    if navigation_found:
        print(f"\n✅ {len(navigation_found)} éléments de navigation trouvés:")
        for line_num, nav_type, line_content in navigation_found[:10]:
            print(f"  Ligne {line_num} ({nav_type}): {line_content[:80]}")

    # Détecter les sections existantes
    print("\n📂 SECTIONS PRINCIPALES DÉTECTÉES:")
    print("-" * 70)

    section_keywords = [
        'chat', 'soumission', 'client', 'entreprise',
        'calendrier', 'configuration', 'fournisseur'
    ]

    sections_found = set()

    for line in lines:
        line_lower = line.lower()
        for keyword in section_keywords:
            if keyword in line_lower and ('if' in line_lower or 'elif' in line_lower or 'def' in line_lower):
                sections_found.add(keyword)

    if sections_found:
        print(f"  Sections trouvées: {', '.join(sorted(sections_found))}")

    # Suggestions
    print("\n" + "="*70)
    print("💡 SUGGESTIONS D'INTÉGRATION")
    print("="*70)

    print("""
OPTION 1 - Si vous utilisez un menu sidebar:
------------------------------------------
Trouvez la ligne qui ressemble à:

    menu = st.sidebar.selectbox("Navigation", [...])

Modifiez-la pour ajouter "📐 TAKEOFF AI":

    menu = st.sidebar.selectbox("Navigation", [
        "💬 Chat Expert",
        "📋 Soumissions",
        "📐 TAKEOFF AI",  # ← NOUVEAU
        "👥 Clients",
        ...
    ])

Puis ajoutez:

    if menu == "📐 TAKEOFF AI":
        show_takeoff_interface()


OPTION 2 - Si vous utilisez des conditions if/elif:
--------------------------------------------------
Ajoutez après les autres sections:

    elif page_selection == "takeoff" or "TAKEOFF" in selected_option:
        show_takeoff_interface()


OPTION 3 - Créer un nouveau fichier de page (recommandé):
--------------------------------------------------------
Créez: pages/3_📐_TAKEOFF_AI.py

Contenu:

    import streamlit as st
    from takeoff_module import show_takeoff_interface

    st.set_page_config(
        page_title="TAKEOFF AI",
        page_icon="📐",
        layout="wide"
    )

    show_takeoff_interface()

Streamlit détectera automatiquement la nouvelle page!

""")

    print("="*70)
    print("✅ ANALYSE TERMINÉE")
    print("="*70)
    print("\nConsultez INSTALLATION.md pour les instructions détaillées")


def check_dependencies():
    """Vérifie si les dépendances sont installées"""

    print("\n" + "="*70)
    print("📦 VÉRIFICATION DES DÉPENDANCES")
    print("="*70)

    required_packages = [
        ('fitz', 'pymupdf', 'PyMuPDF pour lecture PDF'),
        ('numpy', 'numpy', 'NumPy pour calculs'),
        ('pandas', 'pandas', 'Pandas pour tableaux'),
        ('streamlit', 'streamlit', 'Streamlit (déjà installé)'),
    ]

    missing = []

    for import_name, package_name, description in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {description}: OK")
        except ImportError:
            print(f"❌ {description}: MANQUANT")
            missing.append(package_name)

    if missing:
        print(f"\n⚠️ DÉPENDANCES MANQUANTES:")
        print(f"\nInstallez avec:")
        print(f"    pip install {' '.join(missing)}")
    else:
        print("\n✅ Toutes les dépendances sont installées!")


def create_backup(app_file_path):
    """Crée une sauvegarde de app.py"""

    if not os.path.exists(app_file_path):
        return False

    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{app_file_path}.backup_{timestamp}"

    try:
        with open(app_file_path, 'r', encoding='utf-8') as source:
            content = source.read()

        with open(backup_path, 'w', encoding='utf-8') as backup:
            backup.write(content)

        print(f"✅ Sauvegarde créée: {backup_path}")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║        📐 TAKEOFF AI - Assistant d'Intégration EXPERTS IA        ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    # Chemin vers app.py
    app_path = os.path.join(os.path.dirname(__file__), '..', 'app.py')

    # Créer une sauvegarde
    print("\n🔒 SAUVEGARDE DE APP.PY")
    print("=" * 70)
    if create_backup(app_path):
        print("✅ Sauvegarde effectuée avec succès")
    else:
        print("⚠️ Impossible de créer une sauvegarde")

    # Analyser la structure
    analyze_app_structure(app_path)

    # Vérifier les dépendances
    check_dependencies()

    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║  🚀 PROCHAINES ÉTAPES:                                            ║
║                                                                   ║
║  1. Suivez les suggestions ci-dessus pour modifier app.py        ║
║  2. OU créez une page Streamlit dans pages/                      ║
║  3. Installez les dépendances manquantes si nécessaire           ║
║  4. Testez avec: streamlit run app.py                            ║
║  5. Consultez INSTALLATION.md pour plus de détails               ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
