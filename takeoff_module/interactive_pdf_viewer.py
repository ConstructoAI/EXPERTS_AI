"""
Viewer PDF interactif pour TAKEOFF AI Phase 2

Permet de:
- Afficher le PDF avec zoom/pan
- Cliquer pour ajouter des points de mesure
- Dessiner des lignes, polygones, annotations
- Calibration visuelle de l'échelle
- Accrochage automatique aux éléments
"""

import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io
import numpy as np
from typing import List, Tuple, Optional, Dict
import json


class InteractivePDFViewer:
    """Viewer PDF interactif avec fonctionnalités de mesure"""

    def __init__(self):
        self.zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        self.default_zoom_index = 2  # 1.0

    def render_pdf_to_image(self, pdf_path: str, page_num: int = 0, zoom: float = 1.0) -> Image.Image:
        """
        Convertit une page PDF en image PIL

        Args:
            pdf_path: Chemin vers le PDF
            page_num: Numéro de page (0-indexed)
            zoom: Facteur de zoom

        Returns:
            Image PIL de la page
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]

            # Appliquer le zoom
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Convertir en PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            doc.close()
            return img

        except Exception as e:
            st.error(f"Erreur lors du rendu PDF: {e}")
            return None

    def get_pdf_info(self, pdf_path: str) -> Dict:
        """Récupère les informations du PDF"""
        try:
            doc = fitz.open(pdf_path)
            info = {
                'num_pages': doc.page_count,
                'pages': []
            }

            for i in range(doc.page_count):
                page = doc[i]
                rect = page.rect
                info['pages'].append({
                    'page_num': i,
                    'width': rect.width,
                    'height': rect.height
                })

            doc.close()
            return info

        except Exception as e:
            return {'num_pages': 0, 'pages': [], 'error': str(e)}

    def render_interactive(self, pdf_path: str, measurement_tool: str = 'distance'):
        """
        Affiche le viewer PDF interactif avec canvas de dessin

        Args:
            pdf_path: Chemin vers le PDF
            measurement_tool: Outil de mesure actif
        """

        # Initialiser session state pour le viewer
        if 'pdf_viewer_page' not in st.session_state:
            st.session_state.pdf_viewer_page = 0

        if 'pdf_viewer_zoom_index' not in st.session_state:
            st.session_state.pdf_viewer_zoom_index = self.default_zoom_index

        if 'pdf_viewer_temp_points' not in st.session_state:
            st.session_state.pdf_viewer_temp_points = []

        # Obtenir infos PDF
        pdf_info = self.get_pdf_info(pdf_path)

        if pdf_info['num_pages'] == 0:
            st.error("Impossible de charger le PDF")
            return

        # Contrôles de navigation
        col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 2, 2])

        with col1:
            # Sélection de page
            page_num = st.selectbox(
                "Page",
                range(pdf_info['num_pages']),
                index=st.session_state.pdf_viewer_page,
                format_func=lambda x: f"Page {x+1}/{pdf_info['num_pages']}",
                key='pdf_page_selector'
            )
            st.session_state.pdf_viewer_page = page_num

        with col2:
            # Zoom
            zoom_index = st.selectbox(
                "Zoom",
                range(len(self.zoom_levels)),
                index=st.session_state.pdf_viewer_zoom_index,
                format_func=lambda x: f"{int(self.zoom_levels[x]*100)}%",
                key='pdf_zoom_selector'
            )
            st.session_state.pdf_viewer_zoom_index = zoom_index
            current_zoom = self.zoom_levels[zoom_index]

        with col3:
            # Mode de dessin
            drawing_mode = self._get_drawing_mode(measurement_tool)
            st.caption(f"Mode: {drawing_mode}")

        with col4:
            # Couleur de trait
            stroke_color = st.color_picker(
                "Couleur",
                value='#FF0000',
                key='pdf_stroke_color'
            )

        with col5:
            # Effacer les annotations
            if st.button("🗑️ Effacer annotations", key='clear_annotations'):
                st.session_state.pdf_viewer_temp_points = []
                st.rerun()

        # Rendre le PDF en image
        pdf_image = self.render_pdf_to_image(pdf_path, page_num, current_zoom)

        if pdf_image is None:
            return

        # Taille du canvas
        canvas_width = pdf_image.width
        canvas_height = pdf_image.height

        # Informations sur l'outil actif
        tool_instructions = self._get_tool_instructions(measurement_tool)
        st.info(f"🛠️ **{measurement_tool.upper()}** - {tool_instructions}")

        # Canvas interactif avec l'image PDF en arrière-plan
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 0.1)",
            stroke_width=3,
            stroke_color=stroke_color,
            background_image=pdf_image,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode=drawing_mode,
            point_display_radius=5,
            key=f"pdf_canvas_{page_num}_{zoom_index}_{measurement_tool}",
        )

        # Traiter les données du canvas
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data.get("objects", [])

            if objects:
                # Récupérer les points/objets dessinés
                self._process_canvas_objects(objects, measurement_tool, current_zoom)

        # Afficher les mesures en cours
        if st.session_state.pdf_viewer_temp_points:
            st.divider()
            st.caption("**Points en cours:**")

            for i, point in enumerate(st.session_state.pdf_viewer_temp_points):
                st.caption(f"  Point {i+1}: ({point[0]:.1f}, {point[1]:.1f})")

            # Bouton pour finaliser la mesure
            if len(st.session_state.pdf_viewer_temp_points) >= 2:
                if st.button("✅ Créer la mesure", key='finalize_measurement'):
                    self._create_measurement_from_points(
                        st.session_state.pdf_viewer_temp_points,
                        measurement_tool
                    )
                    st.session_state.pdf_viewer_temp_points = []
                    st.success("Mesure créée!")
                    st.rerun()

    def _get_drawing_mode(self, measurement_tool: str) -> str:
        """Retourne le mode de dessin selon l'outil"""
        mode_mapping = {
            'distance': 'line',
            'surface': 'polygon',
            'perimeter': 'polygon',
            'angle': 'line',
            'calibration': 'line',
            'point': 'point'
        }
        return mode_mapping.get(measurement_tool, 'line')

    def _get_tool_instructions(self, measurement_tool: str) -> str:
        """Retourne les instructions pour chaque outil"""
        instructions = {
            'distance': "Tracez une ligne entre 2 points pour mesurer la distance",
            'surface': "Dessinez un polygone en cliquant plusieurs points, double-clic pour terminer",
            'perimeter': "Tracez le contour, double-clic pour fermer et calculer le périmètre",
            'angle': "Tracez 2 lignes pour mesurer l'angle entre elles",
            'calibration': "Tracez une ligne sur une distance connue, puis entrez la valeur réelle",
            'point': "Cliquez pour placer un point de référence"
        }
        return instructions.get(measurement_tool, "Dessinez sur le plan")

    def _process_canvas_objects(self, objects: List[Dict], measurement_tool: str, zoom: float):
        """Traite les objets dessinés sur le canvas"""

        # Extraire les points selon le type d'objet
        for obj in objects:
            obj_type = obj.get('type')

            if obj_type == 'line':
                # Ligne: 2 points
                x1, y1 = obj.get('x1', 0), obj.get('y1', 0)
                x2, y2 = obj.get('x2', 0), obj.get('y2', 0)

                # Ajuster pour le zoom
                points = [
                    (x1 / zoom, y1 / zoom),
                    (x2 / zoom, y2 / zoom)
                ]

                # Stocker temporairement
                if len(points) == 2:
                    st.session_state.pdf_viewer_temp_points = points

            elif obj_type == 'path':
                # Polygone: multiples points
                path = obj.get('path', [])
                points = []

                for segment in path:
                    if len(segment) >= 2:
                        # segment[1] et segment[2] sont x et y
                        x, y = segment[1], segment[2]
                        points.append((x / zoom, y / zoom))

                if points:
                    st.session_state.pdf_viewer_temp_points = points

            elif obj_type == 'circle':
                # Point
                cx, cy = obj.get('left', 0), obj.get('top', 0)
                point = (cx / zoom, cy / zoom)

                if point not in st.session_state.pdf_viewer_temp_points:
                    st.session_state.pdf_viewer_temp_points.append(point)

    def _create_measurement_from_points(self, points: List[Tuple], measurement_tool: str):
        """Crée une mesure à partir des points"""

        from .measurement_tools import MeasurementTools

        tools = st.session_state.get('takeoff_tools', MeasurementTools())
        calibration = st.session_state.get('takeoff_calibration', {'value': 1.0, 'unit': 'pi'})

        # Calculer selon le type de mesure
        if measurement_tool == 'distance' and len(points) >= 2:
            # Distance
            pixel_distance = tools.calculate_distance(points[0], points[1])
            real_distance = tools.apply_calibration(pixel_distance, calibration)

            # Créer la mesure
            new_measure = {
                'label': f"Distance #{len(st.session_state.takeoff_measurements) + 1}",
                'type': 'distance',
                'value': round(real_distance, 2),
                'unit': calibration['unit'],
                'product': st.session_state.get('takeoff_selected_product', {}),
                'points': points,
                'timestamp': st.session_state.get('current_timestamp', '')
            }

            st.session_state.takeoff_measurements.append(new_measure)

        elif measurement_tool == 'surface' and len(points) >= 3:
            # Surface
            pixel_area = tools.calculate_area_shoelace(points)
            real_area = tools.apply_calibration(pixel_area, calibration)

            # Convertir en unité de surface
            unit_surface = calibration['unit'] + '²' if '²' not in calibration['unit'] else calibration['unit']

            new_measure = {
                'label': f"Surface #{len(st.session_state.takeoff_measurements) + 1}",
                'type': 'surface',
                'value': round(real_area, 2),
                'unit': unit_surface,
                'product': st.session_state.get('takeoff_selected_product', {}),
                'points': points,
                'timestamp': st.session_state.get('current_timestamp', '')
            }

            st.session_state.takeoff_measurements.append(new_measure)

        elif measurement_tool == 'perimeter' and len(points) >= 3:
            # Périmètre
            pixel_perimeter = tools.calculate_perimeter(points, closed=True)
            real_perimeter = tools.apply_calibration(pixel_perimeter, calibration)

            new_measure = {
                'label': f"Périmètre #{len(st.session_state.takeoff_measurements) + 1}",
                'type': 'perimeter',
                'value': round(real_perimeter, 2),
                'unit': calibration['unit'],
                'product': st.session_state.get('takeoff_selected_product', {}),
                'points': points,
                'timestamp': st.session_state.get('current_timestamp', '')
            }

            st.session_state.takeoff_measurements.append(new_measure)

        elif measurement_tool == 'angle' and len(points) >= 3:
            # Angle
            angle = tools.calculate_angle(points[0], points[1], points[2])

            new_measure = {
                'label': f"Angle #{len(st.session_state.takeoff_measurements) + 1}",
                'type': 'angle',
                'value': round(angle, 1),
                'unit': '°',
                'product': {},
                'points': points,
                'timestamp': st.session_state.get('current_timestamp', '')
            }

            st.session_state.takeoff_measurements.append(new_measure)

        elif measurement_tool == 'calibration' and len(points) >= 2:
            # Calibration - demander la valeur réelle
            pixel_distance = tools.calculate_distance(points[0], points[1])

            # Stocker pour calibration
            st.session_state.calibration_pending = {
                'pixel_distance': pixel_distance,
                'points': points
            }

    def render_calibration_dialog(self):
        """Affiche le dialogue de calibration"""

        if 'calibration_pending' in st.session_state:
            cal_data = st.session_state.calibration_pending

            st.info(f"📏 Distance mesurée: {cal_data['pixel_distance']:.1f} pixels")

            with st.form("calibration_form"):
                st.write("**Entrez la valeur réelle de cette distance:**")

                col1, col2 = st.columns(2)

                with col1:
                    real_value = st.number_input(
                        "Valeur réelle",
                        min_value=0.01,
                        step=0.1,
                        value=1.0,
                        key='calibration_real_value'
                    )

                with col2:
                    real_unit = st.selectbox(
                        "Unité",
                        options=['pi', 'm', 'ft', 'cm'],
                        key='calibration_real_unit'
                    )

                submitted = st.form_submit_button("✅ Appliquer la calibration")

                if submitted:
                    # Calculer le facteur de calibration
                    calibration_factor = real_value / cal_data['pixel_distance']

                    # Sauvegarder
                    st.session_state.takeoff_calibration = {
                        'value': calibration_factor,
                        'unit': real_unit
                    }

                    # Effacer la calibration en attente
                    del st.session_state.calibration_pending

                    st.success(f"✅ Calibration appliquée: 1 pixel = {calibration_factor:.4f} {real_unit}")
                    st.rerun()
