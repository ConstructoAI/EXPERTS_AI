"""Script de diagnostic pour verifier les soumissions"""
# -*- coding: utf-8 -*-
import sqlite3
import os
import sys

# Forcer UTF-8 pour Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Chemin de la base de donnees
DB_PATH = 'soumissions.db'

print("=== DIAGNOSTIC SOUMISSIONS ===\n")

if not os.path.exists(DB_PATH):
    print(f"[X] ERREUR: La base de donnees {DB_PATH} n'existe pas!")
    exit(1)

print(f"[OK] Base de donnees trouvee: {DB_PATH}\n")

# Connexion
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Verifier la structure de la table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='soumissions'")
if cursor.fetchone():
    print("[OK] Table 'soumissions' existe\n")
else:
    print("[X] Table 'soumissions' n'existe pas!\n")
    conn.close()
    exit(1)

# Compter les soumissions
cursor.execute("SELECT COUNT(*) FROM soumissions")
count = cursor.fetchone()[0]
print(f"[INFO] Nombre total de soumissions: {count}\n")

if count == 0:
    print("[!] Aucune soumission dans la base de donnees!")
    print("\nPossibles causes:")
    print("1. Vous n'avez pas encore genere de soumission")
    print("2. La soumission n'a pas ete sauvegardee (erreur)")
    print("3. Mauvais chemin de base de donnees")
else:
    # Afficher les 10 dernieres soumissions
    print("[LIST] Dernieres soumissions (max 10):\n")
    cursor.execute("""
        SELECT id, numero_soumission, client_nom,
               investissement_total, date_creation, statut
        FROM soumissions
        ORDER BY date_creation DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    for row in rows:
        id, numero, client, montant, date, statut = row
        print(f"  ID: {id}")
        print(f"  N°: {numero}")
        print(f"  Client: {client}")
        print(f"  Montant: {montant:,.2f} $")
        print(f"  Date: {date}")
        print(f"  Statut: {statut}")
        print("  " + "-" * 50)

conn.close()

print("\n=== FIN DU DIAGNOSTIC ===")
