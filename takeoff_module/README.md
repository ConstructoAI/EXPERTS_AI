# 📐 TAKEOFF AI - Module d'Intégration pour EXPERTS IA

## ✅ PHASE 1 & 2 COMPLÉTÉES - Intégration Avancée

### 🎉 Ce qui a été créé:

```
takeoff_module/
├── __init__.py                     ✅ Module principal avec auto-détection Phase 2
├── measurement_tools.py            ✅ Outils de calcul géométrique
├── product_catalog.py              ✅ Gestion catalogue produits
├── integration_bridge.py           ✅ Pont vers soumissions EXPERTS IA
│
├── takeoff_interface.py            ✅ Interface Phase 1 (classique)
├── takeoff_interface_v2.py         ✅ Interface Phase 2 (interactive)
├── interactive_pdf_viewer.py       ✅ Viewer PDF avec canvas
├── snap_system.py                  ✅ Accrochage intelligent (OpenCV)
├── expert_advisor.py               ✅ Intégration 65 profils experts IA
│
├── INSTALLATION.md                 ✅ Guide installation Phase 1
├── PHASE_2_ACTIVATION.md           ✅ Guide activation Phase 2
├── ACTIVER_TAKEOFF_AI.bat          ✅ Script activation Phase 1
├── ACTIVER_TAKEOFF_AI_PHASE2.bat   ✅ Script activation Phase 2
└── README.md                       ✅ Ce fichier
```

---

## 🚀 DÉMARRAGE RAPIDE

### OPTION A - Phase 1 (Basique)

#### Étape 1: Installer les dépendances

```bash
pip install pymupdf numpy
```

**OU** utilisez le script automatique:

```bash
takeoff_module\ACTIVER_TAKEOFF_AI.bat
```

### OPTION B - Phase 2 (Avancée - RECOMMANDÉ)

#### Étape 1: Installer les dépendances Phase 2

```bash
pip install pymupdf numpy streamlit-drawable-canvas opencv-python plotly
```

**OU** utilisez le script automatique:

```bash
takeoff_module\ACTIVER_TAKEOFF_AI_PHASE2.bat
```

📚 **Consultez [PHASE_2_ACTIVATION.md](./PHASE_2_ACTIVATION.md) pour le guide complet**

### Étape 2: Choisir votre méthode d'intégration

**MÉTHODE RECOMMANDÉE** - Créer une nouvelle page Streamlit:

```bash
# Créer le dossier pages s'il n'existe pas
mkdir pages

# Créer le fichier de page
```

Créez: `pages/3_📐_TAKEOFF_AI.py`

```python
import streamlit as st
from takeoff_module import show_takeoff_interface

st.set_page_config(
    page_title="TAKEOFF AI - Mesures",
    page_icon="📐",
    layout="wide"
)

show_takeoff_interface()
```

✅ **C'est tout!** Streamlit détectera automatiquement la nouvelle page.

---

### Étape 3: Lancer l'application

```bash
streamlit run app.py
```

Vous verrez maintenant un nouvel onglet "📐 TAKEOFF_AI" dans la barre latérale!

---

## 📊 FONCTIONNALITÉS DISPONIBLES

| Fonctionnalité | Phase 1 | Phase 2 | Description |
|---|---|---|---|
| Chargement PDF | ✅ | ✅ | Upload et visualisation de plans PDF |
| Ajout manuel mesures | ✅ | ✅ | Formulaire pour saisir mesures |
| Catalogue produits | ✅ | ✅ | 6 catégories avec produits québécois |
| Association produit-mesure | ✅ | ✅ | Lier produits aux mesures |
| Calcul totaux automatique | ✅ | ✅ | Quantités et coûts par produit |
| Export CSV | ✅ | ✅ | Télécharger mesures en CSV |
| Export vers Soumissions | ✅ | ✅ | Intégration EXPERTS IA |
| Gestion catalogue | ✅ | ✅ | Ajouter/supprimer produits |
| Import/Export catalogue | ✅ | ✅ | JSON bidirectionnel |
| **Viewer PDF interactif** | ❌ | ✅ | Canvas avec dessin sur PDF |
| **Calibration visuelle** | ❌ | ✅ | Dialogue interactif d'échelle |
| **Accrochage intelligent** | ❌ | ✅ | Snap auto aux lignes/points (OpenCV) |
| **Conseils IA experts** | ❌ | ✅ | 65 profils EXPERTS IA intégrés |
| **Zoom multi-niveaux** | ❌ | ✅ | 50% à 300% |
| **Navigation multi-pages** | ❌ | ✅ | Tous les plans PDF |
| **Détection de lignes** | ❌ | ✅ | Hough Transform (CV) |

---

## 💡 UTILISATION

### 1. Charger un plan PDF

- Cliquez sur "Charger un plan" (colonne gauche)
- Sélectionnez votre fichier PDF
- Le plan s'affichera dans la colonne centrale

### 2. Ajouter des mesures

**Phase 1 - Mode manuel:**

- Remplissez le formulaire "Ajouter une mesure manuellement"
- Entrez: nom, valeur, unité, type
- Cliquez "✅ Ajouter la mesure"

**Phase 2 - Mode interactif:** ✅ **DISPONIBLE**

- Sélectionnez "🖱️ Interactif (Phase 2)" dans la barre latérale
- Cliquez directement sur le PDF pour dessiner
- Tracez des lignes, polygones, angles avec accrochage intelligent
- Calibration visuelle avec dialogue interactif
- Consultez les experts IA pour des conseils contextuels

📚 **Guide complet:** [PHASE_2_ACTIVATION.md](./PHASE_2_ACTIVATION.md)

### 3. Associer des produits

- Sélectionnez une catégorie dans le catalogue
- Choisissez un produit
- Le produit sera automatiquement associé aux nouvelles mesures

### 4. Gérer le catalogue

- Cliquez "⚙️ Gérer le catalogue"
- Onglet "Produits": voir/supprimer produits existants
- Onglet "Ajouter": créer nouveaux produits/catégories
- Onglet "Import/Export": sauvegarder/charger catalogues JSON

### 5. Exporter vers Soumissions

- Cliquez "📤 Exporter vers Soumission"
- Allez dans l'onglet "Soumissions" d'EXPERTS IA
- Complétez les informations client
- Sauvegardez la soumission

---

## 🗂️ STRUCTURE DES DONNÉES

### Mesure

```python
{
    'label': 'Mur extérieur nord',
    'type': 'distance',  # ou surface, perimeter, angle
    'value': 45.5,
    'unit': 'pi',
    'product': {
        'name': 'Gypse régulier 1/2"',
        'category': 'Gypse',
        'price': 12.0,
        'unit': 'feuille'
    },
    'timestamp': '2025-01-04T14:30:00'
}
```

### Export vers Soumission

Les mesures sont automatiquement converties en format EXPERTS IA:

- **Catégories mappées** selon type de produit
- **Ratios matériaux/main-d'œuvre** appliqués
- **Totaux calculés** avec admin, profit, taxes
- **Traçabilité** via champ `source: 'TAKEOFF_AI'`

---

## 🔧 CONFIGURATION

### Catalogue de produits

Le catalogue par défaut inclut:

- **Béton:** 3 résistances (25/30/35 MPa)
- **Acier d'armature:** Barres 10M/15M/20M + treillis
- **Coffrages:** Contreplaqué, madriers
- **Isolation:** Laine minérale R-12/R-20, polystyrène
- **Gypse:** Régulier, résistant eau, coupe-feu
- **Toiture:** Bardeaux, membranes

Fichier: `takeoff_product_catalog.json`

### Calibration

Par défaut: 1 pixel = 1 pied

Pour modifier:

1. Sélectionnez "🎯 Calibration échelle"
2. Modifiez le facteur et l'unité
3. Phase 2: calibration visuelle interactive

---

## 🔗 INTÉGRATION AVEC EXPERTS IA

### Import automatique dans Soumissions

Le module stocke les données dans `st.session_state.pending_soumission_from_takeoff`

**Pour activer l'import dans la section Soumissions**, ajoutez au début de votre code soumissions:

```python
from takeoff_module.integration_bridge import (
    has_pending_takeoff_soumission,
    get_pending_takeoff_soumission
)

# Dans la fonction/section soumissions
if has_pending_takeoff_soumission():
    st.info("📐 Soumission TAKEOFF AI prête!")

    if st.button("📥 Importer"):
        data = get_pending_takeoff_soumission()
        st.session_state.current_soumission = data
        st.success("✅ Importée!")
```

### Mapping des catégories

| Catégorie TAKEOFF | Catégorie EXPERTS IA |
|---|---|
| Béton, Acier, Coffrages | FONDATION ET STRUCTURE |
| Isolation | ISOLATION ET ÉTANCHÉITÉ |
| Gypse | FINITIONS INTÉRIEURES |
| Toiture | TOITURE |
| Fenestration | CHARPENTE ET ENVELOPPE |
| Revêtement | REVÊTEMENTS EXTÉRIEURS |

---

## 🐛 DÉPANNAGE

### PDF ne s'affiche pas

**Erreur:** `No module named 'fitz'`

**Solution:**
```bash
pip install pymupdf
```

### Catalogue vide

Le catalogue se crée automatiquement au premier lancement.

Si problème, supprimez `takeoff_product_catalog.json` et relancez.

### Export ne fonctionne pas

Vérifiez que `entreprise_config.py` existe dans le dossier parent.

Pour Phase 1, l'export utilise des valeurs par défaut si le module n'est pas accessible.

---

## 📈 FEUILLE DE ROUTE

### ✅ Phase 1 (COMPLÉTÉE - 2025-01-04)

- ✅ Module de base
- ✅ Interface simplifiée
- ✅ Ajout manuel mesures
- ✅ Catalogue produits
- ✅ Export vers soumissions
- ✅ Documentation complète

### ✅ Phase 2 (COMPLÉTÉE - 2025-01-04)

- ✅ Viewer PDF interactif complet avec canvas
- ✅ Mesures par clics/tracés sur PDF
- ✅ Calibration visuelle échelle
- ✅ Accrochage automatique lignes/points (OpenCV)
- ✅ Conseils IA avec 65 profils experts EXPERTS IA
- ✅ Zoom multi-niveaux (50%-300%)
- ✅ Navigation multi-pages
- ✅ Détection de lignes Hough Transform
- ✅ 5 types d'accrochage (points, intersections, extrémités, milieux, perpendiculaire)
- ✅ Guides visuels d'alignement
- ✅ Script d'activation automatique

### 🔜 Phase 3 (2-3 semaines)

- Synchronisation catalogue ↔ fournisseurs EXPERTS IA
- Dashboard analytics
- Export PDF rapports mesures
- Templates de projets
- Historique projets récents
- Optimisations performance

---

## 📞 SUPPORT

### Documentation

- **Installation Phase 1:** [INSTALLATION.md](./INSTALLATION.md)
- **Activation Phase 2:** [PHASE_2_ACTIVATION.md](./PHASE_2_ACTIVATION.md)
- **Code source:** Tous les fichiers sont commentés

### Fichiers importants Phase 1

- `takeoff_interface.py`: Interface classique
- `integration_bridge.py`: Logique export soumissions
- `measurement_tools.py`: Calculs géométriques
- `product_catalog.py`: Gestion catalogue

### Fichiers importants Phase 2

- `takeoff_interface_v2.py`: Interface interactive avancée
- `interactive_pdf_viewer.py`: Viewer PDF avec canvas
- `snap_system.py`: Système d'accrochage intelligent
- `expert_advisor.py`: Intégration experts IA

### Problèmes courants

Consultez la section "🐛 Résolution de problèmes" dans INSTALLATION.md

---

## 📝 CHANGELOG

### v2.0.0 - Phase 2 (2025-01-04)

- ✅ Viewer PDF interactif avec canvas (streamlit-drawable-canvas)
- ✅ Système d'accrochage intelligent (OpenCV)
- ✅ Calibration visuelle interactive
- ✅ Intégration 65 profils experts IA
- ✅ Détection automatique de lignes (Hough Transform)
- ✅ Zoom multi-niveaux et navigation multi-pages
- ✅ 5 types d'accrochage : points, intersections, extrémités, milieux, perpendiculaire
- ✅ Conseils IA contextuels (analyse mesures, recommandations produits, validation calibration)
- ✅ Script d'activation automatique Phase 2
- ✅ Documentation Phase 2 complète

### v1.0.0 - Phase 1 (2025-01-04)

- ✅ Création du module TAKEOFF AI
- ✅ Intégration basique dans EXPERTS IA
- ✅ Interface simplifiée avec ajout manuel
- ✅ Catalogue de produits québécois
- ✅ Export vers soumissions
- ✅ Documentation complète

---

## 📄 LICENCE

Ce module est intégré à EXPERTS IA et suit la même licence.

© 2025 Constructo AI Inc.

---

**Développé avec ❤️ pour les professionnels de la construction québécois**
