"""
Module d'intégration TAKEOFF AI dans EXPERTS IA

Ce module intègre les fonctionnalités de mesure PDF et de quantitatif
de TAKEOFF AI dans l'application EXPERTS IA.

Fonctionnalités Phase 1:
- Visualisation PDF statique
- Ajout manuel de mesures
- Catalogue de produits
- Export vers soumissions EXPERTS IA

Fonctionnalités Phase 2:
- Viewer PDF interactif avec canvas
- Mesures par dessin sur PDF
- Calibration visuelle
- Accrochage intelligent
- Conseils IA avec 65 profils experts
"""

__version__ = "2.0.0"
__author__ = "Constructo AI"

# Importer la Phase 1 (toujours disponible)
from .takeoff_interface import show_takeoff_interface  # Phase 1

# Tenter d'importer la Phase 2 (dépendances optionnelles)
show_takeoff_interface_v2 = None
__phase__ = "1"

try:
    # Vérifier si les dépendances Phase 2 sont installées
    import streamlit_drawable_canvas
    import cv2

    # Si oui, importer la version 2
    from .takeoff_interface_v2 import show_takeoff_interface_v2

    # Exposer la version 2 comme interface par défaut
    show_takeoff_interface = show_takeoff_interface_v2
    __phase__ = "2"

except ImportError as e:
    # Phase 2 non disponible, garder Phase 1
    __phase__ = "1"
    # show_takeoff_interface_v2 reste None

__all__ = [
    'show_takeoff_interface',
    'show_takeoff_interface_v2',
]
