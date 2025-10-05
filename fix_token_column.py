"""
Script pour ajouter la colonne token
"""

import sqlite3
import sys
import io

# Configurer l'encodage pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = 'soumissions.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Ajout de la colonne token...")

try:
    cursor.execute('ALTER TABLE soumissions ADD COLUMN token TEXT')
    print("  OK - Colonne token ajoutée")
except Exception as e:
    print(f"  Déjà existe ou erreur: {e}")

try:
    cursor.execute('CREATE UNIQUE INDEX idx_token_unique ON soumissions(token)')
    print("  OK - Index unique créé")
except Exception as e:
    print(f"  Index existe ou erreur: {e}")

conn.commit()
conn.close()

print("\nFINI ! La colonne token est maintenant disponible.")
