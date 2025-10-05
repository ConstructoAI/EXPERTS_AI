"""
Système d'accrochage intelligent pour TAKEOFF AI Phase 2

Fonctionnalités:
- Détection automatique des lignes dans le PDF
- Accrochage aux points, lignes, intersections
- Guides visuels d'alignement
- Accrochage orthogonal (0°, 45°, 90°)
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
import cv2
from PIL import Image


class SnapSystem:
    """Système d'accrochage intelligent pour mesures précises"""

    def __init__(self, snap_threshold: int = 15):
        """
        Args:
            snap_threshold: Distance en pixels pour activer l'accrochage
        """
        self.snap_threshold = snap_threshold
        self.detected_lines = []
        self.detected_points = []
        self.intersections = []

    def detect_lines_in_image(self, image: Image.Image,
                               min_line_length: int = 50) -> List[Dict]:
        """
        Détecte les lignes dans une image PDF

        Args:
            image: Image PIL du PDF
            min_line_length: Longueur minimale de ligne à détecter

        Returns:
            Liste de lignes détectées
        """

        # Convertir PIL en numpy array
        img_array = np.array(image)

        # Convertir en niveaux de gris si nécessaire
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Détection de contours avec Canny
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Détection de lignes avec Hough Transform probabiliste
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=min_line_length,
            maxLineGap=10
        )

        detected_lines = []

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]

                # Calculer l'angle de la ligne
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

                detected_lines.append({
                    'start': (float(x1), float(y1)),
                    'end': (float(x2), float(y2)),
                    'angle': float(angle),
                    'length': float(np.sqrt((x2-x1)**2 + (y2-y1)**2))
                })

        self.detected_lines = detected_lines
        return detected_lines

    def find_intersections(self, lines: List[Dict]) -> List[Tuple[float, float]]:
        """
        Trouve les intersections entre lignes

        Args:
            lines: Liste de lignes

        Returns:
            Liste de points d'intersection
        """

        intersections = []

        for i, line1 in enumerate(lines):
            for line2 in lines[i+1:]:
                intersection = self._line_intersection(
                    line1['start'], line1['end'],
                    line2['start'], line2['end']
                )

                if intersection:
                    intersections.append(intersection)

        self.intersections = intersections
        return intersections

    def _line_intersection(self, p1: Tuple, p2: Tuple,
                           p3: Tuple, p4: Tuple) -> Optional[Tuple[float, float]]:
        """
        Calcule l'intersection entre deux lignes

        Args:
            p1, p2: Points de la ligne 1
            p3, p4: Points de la ligne 2

        Returns:
            Point d'intersection ou None
        """

        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)

        if abs(denom) < 1e-10:
            return None  # Lignes parallèles

        t = ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / denom
        u = -((x1-x2)*(y1-y3) - (y1-y2)*(x1-x3)) / denom

        # Vérifier si l'intersection est dans les segments
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return (float(x), float(y))

        return None

    def find_snap_point(self, cursor: Tuple[float, float],
                        user_points: List[Tuple] = None) -> Optional[Dict]:
        """
        Trouve le meilleur point d'accrochage

        Args:
            cursor: Position actuelle du curseur
            user_points: Points déjà placés par l'utilisateur

        Returns:
            Dict avec le point d'accrochage et son type
        """

        user_points = user_points or []
        candidates = []

        # 1. Accrochage aux points utilisateur
        for point in user_points:
            dist = self._distance(cursor, point)
            if dist < self.snap_threshold:
                candidates.append({
                    'point': point,
                    'distance': dist,
                    'type': 'user_point',
                    'priority': 1
                })

        # 2. Accrochage aux intersections détectées
        for intersection in self.intersections:
            dist = self._distance(cursor, intersection)
            if dist < self.snap_threshold:
                candidates.append({
                    'point': intersection,
                    'distance': dist,
                    'type': 'intersection',
                    'priority': 2
                })

        # 3. Accrochage aux extrémités de lignes détectées
        for line in self.detected_lines:
            for endpoint in [line['start'], line['end']]:
                dist = self._distance(cursor, endpoint)
                if dist < self.snap_threshold:
                    candidates.append({
                        'point': endpoint,
                        'distance': dist,
                        'type': 'line_endpoint',
                        'priority': 3
                    })

        # 4. Accrochage aux milieux de lignes
        for line in self.detected_lines:
            mid_point = (
                (line['start'][0] + line['end'][0]) / 2,
                (line['start'][1] + line['end'][1]) / 2
            )
            dist = self._distance(cursor, mid_point)
            if dist < self.snap_threshold:
                candidates.append({
                    'point': mid_point,
                    'distance': dist,
                    'type': 'line_midpoint',
                    'priority': 4
                })

        # 5. Accrochage perpendiculaire aux lignes
        for line in self.detected_lines:
            perp_point = self._closest_point_on_line(
                cursor,
                line['start'],
                line['end']
            )

            if perp_point:
                dist = self._distance(cursor, perp_point)
                if dist < self.snap_threshold:
                    candidates.append({
                        'point': perp_point,
                        'distance': dist,
                        'type': 'perpendicular',
                        'priority': 5
                    })

        # Trier par priorité puis par distance
        if candidates:
            candidates.sort(key=lambda x: (x['priority'], x['distance']))
            return candidates[0]

        return None

    def suggest_orthogonal_point(self, p1: Tuple[float, float],
                                 cursor: Tuple[float, float],
                                 angle_tolerance: float = 5.0) -> Optional[Tuple[float, float]]:
        """
        Suggère un point orthogonal (0°, 45°, 90°) par rapport au point précédent

        Args:
            p1: Point de référence
            cursor: Position actuelle du curseur
            angle_tolerance: Tolérance en degrés

        Returns:
            Point ajusté ou None
        """

        dx = cursor[0] - p1[0]
        dy = cursor[1] - p1[1]

        if abs(dx) < 1 and abs(dy) < 1:
            return None

        angle = np.degrees(np.arctan2(dy, dx))

        # Normaliser l'angle entre -180 et 180
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360

        # Angles de référence
        reference_angles = [0, 45, 90, 135, 180, -45, -90, -135]

        # Trouver l'angle le plus proche
        closest_angle = min(reference_angles, key=lambda a: abs(angle - a))

        # Si assez proche, ajuster
        if abs(angle - closest_angle) < angle_tolerance:
            # Calculer la distance
            distance = np.sqrt(dx**2 + dy**2)

            # Calculer le nouveau point sur l'angle orthogonal
            rad = np.radians(closest_angle)
            new_x = p1[0] + distance * np.cos(rad)
            new_y = p1[1] + distance * np.sin(rad)

            return (float(new_x), float(new_y))

        return None

    def get_alignment_guides(self, point: Tuple[float, float],
                            reference_points: List[Tuple]) -> List[Dict]:
        """
        Génère des guides d'alignement visuels

        Args:
            point: Point actuel
            reference_points: Points de référence

        Returns:
            Liste de guides (lignes à afficher)
        """

        guides = []

        for ref_point in reference_points:
            # Guide vertical
            if abs(point[0] - ref_point[0]) < self.snap_threshold:
                guides.append({
                    'type': 'vertical',
                    'x': ref_point[0],
                    'color': 'cyan',
                    'style': 'dashed'
                })

            # Guide horizontal
            if abs(point[1] - ref_point[1]) < self.snap_threshold:
                guides.append({
                    'type': 'horizontal',
                    'y': ref_point[1],
                    'color': 'cyan',
                    'style': 'dashed'
                })

            # Guide diagonal 45°
            dx = abs(point[0] - ref_point[0])
            dy = abs(point[1] - ref_point[1])

            if abs(dx - dy) < self.snap_threshold:
                guides.append({
                    'type': 'diagonal',
                    'from': ref_point,
                    'to': point,
                    'color': 'magenta',
                    'style': 'dashed'
                })

        return guides

    def _distance(self, p1: Tuple, p2: Tuple) -> float:
        """Calcule la distance euclidienne entre 2 points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def _closest_point_on_line(self, point: Tuple,
                               line_start: Tuple,
                               line_end: Tuple) -> Optional[Tuple]:
        """Trouve le point le plus proche sur une ligne"""

        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return line_start

        t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)

        # Limiter au segment
        t = max(0, min(1, t))

        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        return (float(closest_x), float(closest_y))

    def enable_snap_modes(self, modes: List[str]):
        """
        Active/désactive des modes d'accrochage

        Args:
            modes: Liste de modes à activer
                   ['endpoints', 'midpoints', 'intersections',
                    'perpendicular', 'orthogonal', 'parallel']
        """
        self.active_snap_modes = modes

    def get_snap_info(self, snap_result: Dict) -> str:
        """Retourne une description textuelle du snap"""

        if not snap_result:
            return ""

        snap_types = {
            'user_point': "Point utilisateur",
            'intersection': "Intersection",
            'line_endpoint': "Extrémité de ligne",
            'line_midpoint': "Milieu de ligne",
            'perpendicular': "Perpendiculaire",
            'parallel': "Parallèle"
        }

        snap_type = snap_types.get(snap_result['type'], "Point")
        x, y = snap_result['point']

        return f"🎯 {snap_type}: ({x:.1f}, {y:.1f})"
