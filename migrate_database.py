"""
Script de migration pour ajouter les colonnes de lien public
"""

import sqlite3
import sys
import io

# Configurer l'encodage pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = 'soumissions.db'

print("=" * 70)
print("MIGRATION DE LA BASE DE DONNÉES - Ajout Lien Public")
print("=" * 70)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Vérifier les colonnes existantes
cursor.execute("PRAGMA table_info(soumissions)")
colonnes_existantes = [col[1] for col in cursor.fetchall()]

print(f"\nColonnes existantes: {', '.join(colonnes_existantes)}")

nouvelles_colonnes = [
    ('token', 'TEXT UNIQUE'),
    ('lien_public', 'TEXT'),
    ('date_decision', 'TEXT'),
    ('signature_data', 'TEXT'),
    ('signature_nom', 'TEXT'),
    ('signature_date', 'TEXT')
]

print("\nAjout des nouvelles colonnes...")

for nom_col, type_col in nouvelles_colonnes:
    if nom_col not in colonnes_existantes:
        try:
            sql = f'ALTER TABLE soumissions ADD COLUMN {nom_col} {type_col}'
            print(f"  + Ajout de '{nom_col}'...")
            cursor.execute(sql)
            print(f"    OK - '{nom_col}' ajoutée")
        except Exception as e:
            print(f"    ERREUR: {e}")
    else:
        print(f"  ~ '{nom_col}' existe déjà")

# Créer l'index pour token
try:
    print("\nCréation de l'index pour token...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_token ON soumissions(token)')
    print("  OK - Index créé")
except Exception as e:
    print(f"  ERREUR: {e}")

conn.commit()

# Vérifier les nouvelles colonnes
cursor.execute("PRAGMA table_info(soumissions)")
colonnes_finales = [col[1] for col in cursor.fetchall()]

print("\n" + "=" * 70)
print("RÉSULTAT DE LA MIGRATION")
print("=" * 70)
print(f"Colonnes dans la table: {len(colonnes_finales)}")
print(f"Nouvelles colonnes ajoutées: {len(colonnes_finales) - len(colonnes_existantes)}")

# Afficher toutes les colonnes
print("\nToutes les colonnes:")
for col in colonnes_finales:
    marqueur = "✓" if col in [n[0] for n in nouvelles_colonnes] else " "
    print(f"  {marqueur} {col}")

conn.close()

print("\n" + "=" * 70)
print("MIGRATION TERMINÉE !")
print("=" * 70)
print("\nVous pouvez maintenant:")
print("1. Lancer les tests: python test_lien_public.py")
print("2. Démarrer l'application: streamlit run app.py")
print("=" * 70)
