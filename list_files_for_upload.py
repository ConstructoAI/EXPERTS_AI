"""
Script pour lister tous les fichiers du module takeoff_module a uploader sur Hugging Face
"""
import os

print("=" * 70)
print("LISTE DES FICHIERS A UPLOADER SUR HUGGING FACE")
print("=" * 70)
print()

# Chemin du dossier takeoff_module
base_path = r"C:\$WorkingFolder\Engineering Data\OneDrive - constructoai.ca\10. GITHUB\CONSTRUCTO AI\EXPERTS_AI-main"
takeoff_path = os.path.join(base_path, "takeoff_module")

print(f"Dossier source: {takeoff_path}")
print()

if not os.path.exists(takeoff_path):
    print("[ERREUR] Le dossier takeoff_module n'existe pas!")
    exit(1)

# Lister tous les fichiers
print("FICHIERS A UPLOADER DANS: takeoff_module/")
print("-" * 70)

files = []
for item in sorted(os.listdir(takeoff_path)):
    full_path = os.path.join(takeoff_path, item)

    # Ignorer __pycache__ et fichiers temporaires
    if item == "__pycache__" or item.endswith('.pyc') or item.startswith('.'):
        continue

    if os.path.isfile(full_path):
        size = os.path.getsize(full_path)
        size_kb = size / 1024

        # Marquer les fichiers critiques
        critical = ""
        if item == "__init__.py":
            critical = " [CRITIQUE - REQUIS!]"
        elif item.endswith(".py"):
            critical = " [IMPORTANT]"

        print(f"  {item:<40} {size_kb:>8.1f} KB{critical}")
        files.append(item)

print("-" * 70)
print(f"TOTAL: {len(files)} fichiers a uploader")
print()

# Afficher les fichiers critiques
print("FICHIERS CRITIQUES (obligatoires):")
print("-" * 70)
critical_files = [
    "__init__.py",
    "takeoff_interface.py",
    "measurement_tools.py",
    "product_catalog.py"
]

for f in critical_files:
    if f in files:
        print(f"  [OK] {f}")
    else:
        print(f"  [MANQUANT!] {f}")

print()

# Afficher les fichiers optionnels Phase 2
print("FICHIERS PHASE 2 (optionnels mais recommandes):")
print("-" * 70)
phase2_files = [
    "takeoff_interface_v2.py",
    "interactive_pdf_viewer.py",
    "snap_system.py"
]

for f in phase2_files:
    if f in files:
        print(f"  [OK] {f}")
    else:
        print(f"  [ABSENT] {f}")

print()

# Afficher les fichiers de documentation
print("FICHIERS DOCUMENTATION (optionnels):")
print("-" * 70)
doc_files = [
    "README.md",
    "INSTALLATION.md",
    "PHASE_2_ACTIVATION.md",
    "TEST_RESULTS.md"
]

for f in doc_files:
    if f in files:
        print(f"  [OK] {f}")
    else:
        print(f"  [ABSENT] {f}")

print()
print("=" * 70)
print("COMMANDE D'UPLOAD RECOMMANDEE")
print("=" * 70)
print()
print("Methode 1: Via Git (recommande)")
print("-" * 70)
print("cd VOTRE_SPACE_HF")
print(f'xcopy "{takeoff_path}" takeoff_module\\ /E /I')
print("git add takeoff_module/")
print('git commit -m "Ajout module TAKEOFF AI avec zoom"')
print("git push")
print()

print("Methode 2: Via Hugging Face CLI")
print("-" * 70)
print("huggingface-cli login")
print(f"cd \"{base_path}\"")
print("huggingface-cli upload VOTRE-USER/VOTRE-SPACE ./takeoff_module takeoff_module/ --repo-type=space")
print()

print("=" * 70)
print("VERIFICATION POST-UPLOAD")
print("=" * 70)
print()
print("1. Verifiez sur: https://huggingface.co/spaces/VOTRE-USER/VOTRE-SPACE/tree/main/takeoff_module")
print(f"2. Vous devriez voir {len(files)} fichiers")
print("3. Verifiez que __init__.py est present (fichier critique)")
print("4. Attendez que le Space redemarre (2-3 minutes)")
print("5. Testez l'onglet Takeoff AI dans l'application")
print()
