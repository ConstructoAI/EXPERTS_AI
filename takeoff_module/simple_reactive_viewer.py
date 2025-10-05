"""
Visualiseur PDF interactif avec support complet des fonctionnalités TAKEOFF AI
- Clics interactifs pour calibration et mesures
- Mode Orthogonal (ORTHO) avec guides visuels
- Snap automatique aux points existants
- Contrôles de transparence
- Détection visuelle des lignes
Version améliorée pour EXPERTS_AI
"""

import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime


def render_pdf_viewer(pdf_path: str, current_page: int, measurements: List[Dict],
                     selected_tool: str, calibration: Dict, zoom: float = 1.5):
    """
    Affiche le PDF avec gestion interactive complète

    Args:
        pdf_path: Chemin vers le fichier PDF
        current_page: Numéro de page actuelle (0-indexed)
        measurements: Liste des mesures existantes
        selected_tool: Outil sélectionné ('distance', 'surface', 'perimeter', 'angle', 'calibration')
        calibration: Dict avec 'value' et 'unit'
        zoom: Niveau de zoom (1.0 = 100%)
    """

    # État du viewer dans session_state
    if 'pdf_viewer_state' not in st.session_state:
        st.session_state.pdf_viewer_state = {
            'temp_points': [],
            'last_page': current_page,
            'last_tool': selected_tool,
            'last_zoom': zoom,
            'ortho_active': False,
            'snap_enabled': True,
            'transparency_adjustment': 0
        }

    viewer_state = st.session_state.pdf_viewer_state

    # Reset des points si changement de page, outil ou zoom
    if (viewer_state['last_page'] != current_page or
        viewer_state['last_tool'] != selected_tool or
        abs(viewer_state['last_zoom'] - zoom) > 0.01):
        viewer_state['temp_points'] = []
        viewer_state['last_page'] = current_page
        viewer_state['last_tool'] = selected_tool
        viewer_state['last_zoom'] = zoom

    # Configuration des outils
    tool_configs = {
        'distance': {'max_points': 2, 'color': '#FF0000', 'label': 'Distance'},
        'surface': {'max_points': 99, 'color': '#00FF00', 'label': 'Surface'},
        'perimeter': {'max_points': 99, 'color': '#0000FF', 'label': 'Périmètre'},
        'angle': {'max_points': 3, 'color': '#FF00FF', 'label': 'Angle'},
        'calibration': {'max_points': 2, 'color': '#FFA500', 'label': 'Calibration'}
    }

    config = tool_configs.get(selected_tool, tool_configs['distance'])

    # ===== INTERFACE DE CONTRÔLE AVANCÉE =====
    st.markdown("#### 🎮 Contrôles Avancés")

    # Ligne 1: Info + Boutons de base
    col_info, col_clear, col_validate = st.columns([3, 1, 1])

    with col_info:
        nb_points = len(viewer_state['temp_points'])
        info_parts = [f"🎯 {config['label']} - {nb_points} point(s)"]

        if viewer_state.get('ortho_active', False):
            info_parts.append("**ORTHO**")
        if viewer_state.get('snap_enabled', True):
            info_parts.append("**SNAP**")

        st.info(" | ".join(info_parts))

    with col_clear:
        if st.button("🗑️ Effacer", use_container_width=True, disabled=nb_points == 0, key=f"clear_points_{current_page}_{selected_tool}"):
            viewer_state['temp_points'] = []
            st.rerun()

    with col_validate:
        min_points = 2 if selected_tool in ['distance', 'calibration'] else 3
        can_validate = nb_points >= min_points

        if st.button("✅ Valider", use_container_width=True, disabled=not can_validate, type="primary", key=f"validate_measure_{current_page}_{selected_tool}"):
            success = _process_measurement(
                selected_tool,
                viewer_state['temp_points'],
                measurements,
                current_page,
                calibration,
                zoom
            )

            if success:
                viewer_state['temp_points'] = []
                st.rerun()

    # Ligne 2: Options avancées
    col_ortho, col_snap, col_transparency = st.columns(3)

    with col_ortho:
        ortho_enabled = st.checkbox(
            "🔲 Mode Orthogonal",
            value=viewer_state.get('ortho_active', False),
            help="Contraint les lignes aux angles 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°",
            key="ortho_checkbox"
        )
        viewer_state['ortho_active'] = ortho_enabled

    with col_snap:
        snap_enabled = st.checkbox(
            "🧲 Snap automatique",
            value=viewer_state.get('snap_enabled', True),
            help="Accroche automatiquement aux points existants des mesures",
            key="snap_checkbox"
        )
        viewer_state['snap_enabled'] = snap_enabled

    with col_transparency:
        transparency = st.slider(
            "👁️ Transparence",
            min_value=-100,
            max_value=100,
            value=viewer_state.get('transparency_adjustment', 0),
            step=10,
            help="Ajuster la transparence des mesures affichées",
            key="transparency_slider"
        )
        viewer_state['transparency_adjustment'] = transparency

    # ===== AFFICHAGE DU PDF INTERACTIF =====
    try:
        import fitz  # PyMuPDF
        import io

        pdf_doc = fitz.open(pdf_path)
        page = pdf_doc[current_page]

        # Rendu avec zoom
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Convertir en PIL Image
        img_data = pix.tobytes("png")
        base_img = Image.open(io.BytesIO(img_data))
        pdf_doc.close()

        # Dessiner sur l'image
        img = base_img.copy()
        draw = ImageDraw.Draw(img, 'RGBA')

        # 1. Indicateur ORTHO si actif
        if viewer_state.get('ortho_active', False):
            _draw_ortho_indicator(draw)

        # 2. Mesures existantes de cette page
        page_measurements = [m for m in measurements if m.get('page_number', m.get('page', 0)) == current_page]
        for measure in page_measurements:
            _draw_measurement(draw, measure, zoom, transparency)

        # 3. Points temporaires en cours
        if viewer_state['temp_points']:
            _draw_temp_points(
                draw,
                viewer_state['temp_points'],
                selected_tool,
                config['color'],
                viewer_state.get('ortho_active', False)
            )

        # 4. Récupérer tous les points existants pour le snap
        all_existing_points = []
        if viewer_state.get('snap_enabled', True):
            for measure in page_measurements:
                points = measure.get('points', [])
                if points:
                    # Ajuster les points au zoom actuel
                    saved_zoom = measure.get('zoom_level', 1.0)
                    ratio = zoom / saved_zoom
                    adjusted = [(p[0] * ratio, p[1] * ratio) for p in points]
                    all_existing_points.extend(adjusted)

        # Afficher l'image interactive
        clicked = streamlit_image_coordinates(
            img,
            key=f"pdf_interactive_{current_page}_{selected_tool}_{nb_points}_{zoom}_{ortho_enabled}_{snap_enabled}"
        )

        # Traiter le clic
        if clicked and clicked.get('x') is not None and clicked.get('y') is not None:
            x, y = float(clicked['x']), float(clicked['y'])

            # Appliquer le snap si activé
            if viewer_state.get('snap_enabled', True) and all_existing_points:
                snapped = _find_snap_point((x, y), all_existing_points, threshold=15.0)
                if snapped:
                    x, y = snapped
                    st.success(f"🧲 Snap activé à ({x:.1f}, {y:.1f})")

            # Appliquer l'ortho si activé et qu'il y a déjà un point
            if viewer_state.get('ortho_active', False) and len(viewer_state['temp_points']) > 0:
                last_point = viewer_state['temp_points'][-1]
                x, y = _calculate_ortho_point(last_point, (x, y))

            # Éviter les doublons (clics trop proches)
            is_duplicate = False
            for px, py in viewer_state['temp_points']:
                if abs(px - x) < 10 and abs(py - y) < 10:
                    is_duplicate = True
                    break

            if not is_duplicate:
                viewer_state['temp_points'].append((x, y))

                # Afficher le nombre de points ajoutés
                nb_current = len(viewer_state['temp_points'])
                st.info(f"✓ Point {nb_current} ajouté à ({x:.1f}, {y:.1f})")

                # Auto-validation pour distance/angle/calibration (2 points)
                if selected_tool in ['distance', 'angle', 'calibration'] and nb_current >= config['max_points']:
                    success = _process_measurement(
                        selected_tool,
                        viewer_state['temp_points'],
                        measurements,
                        current_page,
                        calibration,
                        zoom
                    )

                    if success:
                        viewer_state['temp_points'] = []

                st.rerun()

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du PDF: {str(e)}")
        st.info("Assurez-vous que PyMuPDF (fitz) est installé: `pip install PyMuPDF`")


def _draw_ortho_indicator(draw):
    """Dessine l'indicateur ORTHO en haut à gauche"""
    ortho_box = (10, 10, 100, 40)
    draw.rectangle(ortho_box, fill=(255, 165, 0, 220), outline=(255, 255, 255, 255), width=2)
    draw.text((25, 18), "ORTHO", fill=(255, 255, 255, 255))


def _draw_temp_points(draw, points: List[Tuple[float, float]], tool: str, color: str, ortho_active: bool):
    """Dessine les points temporaires en cours de saisie"""
    if not points:
        return

    # Convertir couleur hex en RGB
    rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    rgba = rgb + (200,)

    # Lignes entre les points
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=rgba, width=3)

    # Mode ortho : afficher les guides si actif et qu'il y a au moins 1 point
    if ortho_active and len(points) > 0:
        _draw_ortho_guides(draw, points[-1])

    # Pour les surfaces/périmètres, ligne pointillée pour fermer
    if tool in ['surface', 'perimeter'] and len(points) >= 3:
        _draw_dashed_line(draw, points[-1], points[0], rgba)

    # Dessiner les points
    for i, (px, py) in enumerate(points):
        # Cercle blanc de fond
        draw.ellipse([px-8, py-8, px+8, py+8], fill=(255, 255, 255, 220), outline=(255, 255, 255, 255), width=2)
        # Point coloré
        draw.ellipse([px-6, py-6, px+6, py+6], fill=rgba, outline='black', width=1)
        # Numéro
        text = str(i+1)
        bbox = draw.textbbox((px+12, py-12), text)
        draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], fill=(255, 255, 255, 240))
        draw.text((px+12, py-12), text, fill='black')


def _draw_ortho_guides(draw, last_point: Tuple[float, float]):
    """Dessine les guides orthogonaux depuis le dernier point"""
    guide_color = (128, 128, 128, 100)
    guide_length = 120

    # Lignes guides pour les 8 directions
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        angle_rad = math.radians(angle)
        end_x = last_point[0] + guide_length * math.cos(angle_rad)
        end_y = last_point[1] + guide_length * math.sin(angle_rad)

        # Ligne guide pointillée
        _draw_dashed_line(draw, last_point, (end_x, end_y), guide_color)

        # Afficher l'angle
        text_x = last_point[0] + (guide_length * 0.7) * math.cos(angle_rad)
        text_y = last_point[1] + (guide_length * 0.7) * math.sin(angle_rad)
        draw.text((text_x-10, text_y-10), f"{angle}°", fill=(128, 128, 128, 220))


def _draw_measurement(draw, measure: Dict, current_zoom: float, transparency_adj: int = 0):
    """Dessine une mesure sauvegardée sur le plan"""
    points = measure.get('points', [])
    if not points:
        return

    # Ajuster les points selon le zoom
    saved_zoom = measure.get('zoom_level', 1.0)
    ratio = current_zoom / saved_zoom
    adjusted_points = [(p[0] * ratio, p[1] * ratio) for p in points]

    # Couleur
    measure_type = measure.get('type', 'distance')
    type_colors = {
        'distance': '#FF0000',
        'surface': '#00FF00',
        'perimeter': '#0000FF',
        'angle': '#FF00FF',
        'calibration': '#FFA500'
    }
    color = measure.get('color', type_colors.get(measure_type, '#000000'))

    # Convertir en RGBA
    rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

    # Transparence selon le type + ajustement utilisateur
    alpha_levels = {
        'distance': 180,
        'angle': 180,
        'surface': 80,
        'perimeter': 120,
        'calibration': 200
    }
    base_alpha = alpha_levels.get(measure_type, 150)
    alpha = max(30, min(255, base_alpha + transparency_adj))
    rgba = rgb + (alpha,)

    # Dessiner selon le type
    if measure_type == 'distance' and len(adjusted_points) >= 2:
        # Ligne
        draw.line([adjusted_points[0], adjusted_points[1]], fill=rgba, width=3)
        # Points
        for px, py in adjusted_points[:2]:
            draw.ellipse([px-5, py-5, px+5, py+5], fill=rgba, outline=(255, 255, 255, 200), width=1)

        # Label au milieu
        label = measure.get('label', '')
        product = measure.get('product', {})
        product_name = product.get('name', '')
        display_text = f"{label} - {product_name}" if label and product_name else (label or product_name)

        if display_text:
            mid_x = (adjusted_points[0][0] + adjusted_points[1][0]) / 2
            mid_y = (adjusted_points[0][1] + adjusted_points[1][1]) / 2
            _draw_text_with_outline(draw, display_text, mid_x, mid_y - 25)

    elif measure_type in ['surface', 'perimeter'] and len(adjusted_points) >= 3:
        # Polygone
        if measure_type == 'surface':
            draw.polygon(adjusted_points, fill=rgba[:3] + (max(30, min(100, 50 + transparency_adj)),), outline=rgba)

        # Contour
        for i in range(len(adjusted_points)):
            j = (i + 1) % len(adjusted_points)
            draw.line([adjusted_points[i], adjusted_points[j]], fill=rgba, width=3)

        # Points
        for px, py in adjusted_points:
            draw.ellipse([px-4, py-4, px+4, py+4], fill=rgba, outline=(255, 255, 255, 200), width=1)

        # Label au centre
        label = measure.get('label', '')
        product = measure.get('product', {})
        product_name = product.get('name', '')
        display_text = f"{label} - {product_name}" if label and product_name else (label or product_name)

        if display_text:
            center_x = sum(p[0] for p in adjusted_points) / len(adjusted_points)
            center_y = sum(p[1] for p in adjusted_points) / len(adjusted_points)
            _draw_text_with_outline(draw, display_text, center_x, center_y)

    elif measure_type == 'angle' and len(adjusted_points) >= 3:
        # Deux lignes
        draw.line([adjusted_points[0], adjusted_points[1]], fill=rgba, width=3)
        draw.line([adjusted_points[1], adjusted_points[2]], fill=rgba, width=3)

        # Points (sommet plus gros)
        for i, (px, py) in enumerate(adjusted_points[:3]):
            size = 6 if i == 1 else 5
            draw.ellipse([px-size, py-size, px+size, py+size], fill=rgba, outline=(255, 255, 255, 200), width=1)

        # Label près du sommet
        label = measure.get('label', '')
        value = measure.get('value', 0)
        display_text = f"{label}: {value:.1f}°" if label else f"{value:.1f}°"
        _draw_text_with_outline(draw, display_text, adjusted_points[1][0] + 25, adjusted_points[1][1] - 25)


def _draw_text_with_outline(draw, text: str, x: float, y: float):
    """Dessine du texte avec contour blanc pour lisibilité"""
    # Contour blanc
    outline_offsets = [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2)]
    for dx, dy in outline_offsets:
        try:
            draw.text((x + dx, y + dy), text, fill=(255, 255, 255, 255), anchor="mm")
        except:
            draw.text((x + dx - len(text)*4, y + dy), text, fill=(255, 255, 255, 255))

    # Texte principal en noir
    try:
        draw.text((x, y), text, fill=(0, 0, 0, 255), anchor="mm")
    except:
        draw.text((x - len(text)*4, y), text, fill=(0, 0, 0, 255))


def _draw_dashed_line(draw, start: Tuple[float, float], end: Tuple[float, float], color):
    """Dessine une ligne pointillée"""
    x1, y1 = start
    x2, y2 = end

    length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    if length == 0:
        return

    segments = max(int(length / 10), 1)

    for i in range(0, segments, 2):
        t1 = i / segments
        t2 = min((i + 1) / segments, 1)

        sx = x1 + t1 * (x2 - x1)
        sy = y1 + t1 * (y2 - y1)
        ex = x1 + t2 * (x2 - x1)
        ey = y1 + t2 * (y2 - y1)

        draw.line([(sx, sy), (ex, ey)], fill=color, width=2)


def _calculate_ortho_point(last_point: Tuple[float, float], current_point: Tuple[float, float]) -> Tuple[float, float]:
    """Calcule le point orthogonal le plus proche (0°, 45°, 90°, etc.)"""
    dx = current_point[0] - last_point[0]
    dy = current_point[1] - last_point[1]

    # Calculer l'angle
    angle = math.atan2(dy, dx)
    angle_deg = math.degrees(angle)

    # Angles orthogonaux possibles
    ortho_angles = [0, 45, 90, 135, 180, 225, 270, 315]

    # Normaliser l'angle entre 0 et 360
    if angle_deg < 0:
        angle_deg += 360

    # Trouver l'angle orthogonal le plus proche
    closest_angle = min(ortho_angles, key=lambda a: min(abs(a - angle_deg), abs(a - angle_deg + 360), abs(a - angle_deg - 360)))

    # Calculer la distance
    distance = math.sqrt(dx**2 + dy**2)

    # Calculer le nouveau point selon l'angle orthogonal
    angle_rad = math.radians(closest_angle)
    new_x = last_point[0] + distance * math.cos(angle_rad)
    new_y = last_point[1] + distance * math.sin(angle_rad)

    return (new_x, new_y)


def _find_snap_point(cursor: Tuple[float, float], existing_points: List[Tuple[float, float]],
                    threshold: float = 15.0) -> Optional[Tuple[float, float]]:
    """Trouve le point d'accrochage le plus proche"""
    min_distance = threshold
    snap_point = None

    for point in existing_points:
        dist = math.sqrt((cursor[0] - point[0])**2 + (cursor[1] - point[1])**2)
        if dist < min_distance:
            min_distance = dist
            snap_point = point

    return snap_point


def _process_measurement(tool: str, points: List[Tuple[float, float]],
                        measurements: List[Dict], page: int,
                        calibration: Dict, zoom: float) -> bool:
    """
    Traite une mesure complète ou une calibration

    Returns:
        True si succès, False si erreur
    """
    if not points or len(points) < 2:
        return False

    cal_value = calibration.get('value', 1.0)
    cal_unit = calibration.get('unit', 'pi')

    try:
        if tool == 'calibration':
            # Mode calibration : ouvrir dialogue
            dist_pixels = math.sqrt((points[1][0] - points[0][0])**2 + (points[1][1] - points[0][1])**2)
            st.session_state.calibration_pixels = dist_pixels
            st.session_state.calibration_points = points
            st.session_state.show_calibration_dialog = True
            st.success(f"✅ Ligne de calibration tracée ({dist_pixels:.1f} pixels). Définissez la distance réelle.")
            return True

        elif tool == 'distance' and len(points) >= 2:
            # Calcul distance
            dist_pixels = math.sqrt((points[1][0] - points[0][0])**2 + (points[1][1] - points[0][1])**2)
            value_real = dist_pixels * cal_value

            measurement = {
                'type': 'distance',
                'label': f"Distance_{len([m for m in measurements if m.get('type') == 'distance']) + 1}",
                'value': value_real,
                'unit': cal_unit,
                'page_number': page,
                'points': points[:2],
                'zoom_level': zoom,
                'color': '#FF0000',
                'product': st.session_state.get('takeoff_selected_product', {}),
                'timestamp': datetime.now().isoformat()
            }

            measurements.append(measurement)
            st.success(f"✅ {measurement['label']}: {value_real:.2f} {cal_unit}")
            return True

        elif tool == 'surface' and len(points) >= 3:
            # Calcul aire (formule du lacet)
            area_pixels = 0.0
            n = len(points)
            for i in range(n):
                j = (i + 1) % n
                area_pixels += points[i][0] * points[j][1]
                area_pixels -= points[j][0] * points[i][1]
            area_pixels = abs(area_pixels) / 2.0

            value_real = area_pixels * cal_value * cal_value
            unit = f"{cal_unit}²" if '²' not in cal_unit else cal_unit

            measurement = {
                'type': 'surface',
                'label': f"Surface_{len([m for m in measurements if m.get('type') == 'surface']) + 1}",
                'value': value_real,
                'unit': unit,
                'page_number': page,
                'points': points[:],
                'zoom_level': zoom,
                'color': '#00FF00',
                'product': st.session_state.get('takeoff_selected_product', {}),
                'timestamp': datetime.now().isoformat()
            }

            measurements.append(measurement)
            st.success(f"✅ {measurement['label']}: {value_real:.2f} {unit}")
            return True

        elif tool == 'perimeter' and len(points) >= 2:
            # Calcul périmètre (somme des segments)
            perim_pixels = 0.0
            for i in range(len(points) - 1):
                perim_pixels += math.sqrt(
                    (points[i+1][0] - points[i][0])**2 +
                    (points[i+1][1] - points[i][1])**2
                )

            value_real = perim_pixels * cal_value

            measurement = {
                'type': 'perimeter',
                'label': f"Périmètre_{len([m for m in measurements if m.get('type') == 'perimeter']) + 1}",
                'value': value_real,
                'unit': cal_unit,
                'page_number': page,
                'points': points[:],
                'zoom_level': zoom,
                'color': '#0000FF',
                'product': st.session_state.get('takeoff_selected_product', {}),
                'timestamp': datetime.now().isoformat()
            }

            measurements.append(measurement)
            st.success(f"✅ {measurement['label']}: {value_real:.2f} {cal_unit}")
            return True

        elif tool == 'angle' and len(points) >= 3:
            # Calcul angle (produit vectoriel)
            v1 = (points[0][0] - points[1][0], points[0][1] - points[1][1])
            v2 = (points[2][0] - points[1][0], points[2][1] - points[1][1])

            dot = v1[0] * v2[0] + v1[1] * v2[1]
            det = v1[0] * v2[1] - v1[1] * v2[0]
            angle_value = abs(math.degrees(math.atan2(det, dot)))

            measurement = {
                'type': 'angle',
                'label': f"Angle_{len([m for m in measurements if m.get('type') == 'angle']) + 1}",
                'value': angle_value,
                'unit': '°',
                'page_number': page,
                'points': points[:3],
                'zoom_level': zoom,
                'color': '#FF00FF',
                'product': {},
                'timestamp': datetime.now().isoformat()
            }

            measurements.append(measurement)
            st.success(f"✅ {measurement['label']}: {angle_value:.2f}°")
            return True

        return False

    except Exception as e:
        st.error(f"❌ Erreur lors du traitement: {str(e)}")
        return False


def show_calibration_dialog():
    """Affiche le dialogue de calibration (à appeler depuis l'interface principale)"""
    if not st.session_state.get('show_calibration_dialog', False):
        return

    st.markdown("### 🎯 Calibration du Plan")

    with st.form("calibration_form"):
        st.info(f"Ligne tracée: {st.session_state.calibration_pixels:.1f} pixels")

        # Sélection du type d'unité
        unit_type = st.radio(
            "Type d'unité",
            options=['pieds-pouces', 'decimal', 'metrique'],
            format_func=lambda x: {
                'pieds-pouces': "📐 Pieds-Pouces (ex: 10'-6\")",
                'decimal': "📏 Décimal (ex: 10.5 pi ou 126 po)",
                'metrique': "📊 Métrique (cm, m, mm)"
            }.get(x, x),
            horizontal=True
        )

        st.divider()

        if unit_type == 'pieds-pouces':
            # Format pieds-pouces
            st.markdown("**Format: Pieds-Pouces**")
            col1, col2 = st.columns(2)

            with col1:
                feet = st.number_input(
                    "Pieds",
                    min_value=0,
                    value=10,
                    step=1,
                    help="Nombre de pieds"
                )

            with col2:
                inches = st.number_input(
                    "Pouces",
                    min_value=0.0,
                    max_value=11.999,
                    value=0.0,
                    step=0.125,
                    format="%.3f",
                    help="Nombre de pouces (0-11.999)"
                )

            # Calculer la distance totale en pieds
            real_distance = feet + (inches / 12.0)
            unit = 'pi'

            st.caption(f"✓ Distance totale: **{feet}'-{inches:.3f}\"** = **{real_distance:.4f} pieds**")

        elif unit_type == 'decimal':
            # Format décimal
            col1, col2 = st.columns(2)

            with col1:
                real_distance = st.number_input(
                    "Distance",
                    min_value=0.01,
                    value=10.0,
                    step=0.1,
                    format="%.3f",
                    help="Distance en format décimal"
                )

            with col2:
                unit = st.selectbox(
                    "Unité",
                    options=['pi', 'po', 'ft', 'in'],
                    format_func=lambda x: {
                        'pi': 'Pieds (pi)',
                        'po': 'Pouces (po)',
                        'ft': 'Pieds (ft)',
                        'in': 'Pouces (in)'
                    }.get(x, x)
                )

        else:  # metrique
            # Format métrique
            col1, col2 = st.columns(2)

            with col1:
                real_distance = st.number_input(
                    "Distance",
                    min_value=0.01,
                    value=100.0,
                    step=1.0,
                    help="Distance en unités métriques"
                )

            with col2:
                unit = st.selectbox(
                    "Unité",
                    options=['cm', 'm', 'mm'],
                    format_func=lambda x: {
                        'cm': 'Centimètres (cm)',
                        'm': 'Mètres (m)',
                        'mm': 'Millimètres (mm)'
                    }.get(x, x)
                )

        col_cancel, col_submit = st.columns(2)

        with col_cancel:
            if st.form_submit_button("❌ Annuler", use_container_width=True):
                st.session_state.show_calibration_dialog = False
                st.rerun()

        with col_submit:
            if st.form_submit_button("✅ Valider Calibration", use_container_width=True, type="primary"):
                # Calculer le facteur de calibration
                cal_factor = real_distance / st.session_state.calibration_pixels

                # Avertir si le facteur semble anormal
                if cal_factor > 10:
                    st.warning(f"⚠️ Attention: Facteur de calibration très élevé ({cal_factor:.4f} {unit}/pixel). Vérifiez vos valeurs.")
                elif cal_factor < 0.0001:
                    st.warning(f"⚠️ Attention: Facteur de calibration très faible ({cal_factor:.6f} {unit}/pixel). Vérifiez vos valeurs.")

                # Mettre à jour la calibration
                st.session_state.takeoff_calibration = {
                    'value': cal_factor,
                    'unit': unit
                }

                st.session_state.show_calibration_dialog = False
                st.success(f"✅ Calibration réussie! Facteur: {cal_factor:.6f} {unit}/pixel")
                st.rerun()
