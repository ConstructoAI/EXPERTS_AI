"""
Intégration des 65 profils experts d'EXPERTS IA dans TAKEOFF AI Phase 2

Permet d'obtenir des conseils IA contextuels basés sur les mesures effectuées
"""

import streamlit as st
from typing import List, Dict, Optional


class TakeoffExpertAdvisor:
    """Conseiller expert intégré pour TAKEOFF AI"""

    def __init__(self):
        """Initialise le conseiller expert"""
        self.expert_advisor = None
        self.profile_manager = None
        self._initialize_experts()

    def _initialize_experts(self):
        """Initialise l'accès aux experts d'EXPERTS IA"""
        try:
            # Importer les modules d'EXPERTS IA
            from expert_logic import ExpertAdvisor, ExpertProfileManager

            # Vérifier si l'API key est disponible
            if 'expert_advisor' in st.session_state:
                self.expert_advisor = st.session_state.expert_advisor
            else:
                # Créer une nouvelle instance si API key disponible
                api_key = st.session_state.get('anthropic_api_key')
                if api_key:
                    self.expert_advisor = ExpertAdvisor(api_key)
                    st.session_state.expert_advisor = self.expert_advisor

            # Charger le gestionnaire de profils
            if 'profile_manager' in st.session_state:
                self.profile_manager = st.session_state.profile_manager
            else:
                self.profile_manager = ExpertProfileManager()
                st.session_state.profile_manager = self.profile_manager

        except ImportError as e:
            st.warning(f"⚠️ Impossible de charger les experts EXPERTS IA: {e}")
            self.expert_advisor = None
            self.profile_manager = None

    def is_available(self) -> bool:
        """Vérifie si le système expert est disponible"""
        return self.expert_advisor is not None and self.profile_manager is not None

    def get_available_profiles(self) -> List[str]:
        """Retourne la liste des profils experts disponibles"""
        if not self.profile_manager:
            return []

        try:
            profiles = self.profile_manager.get_all_profiles()
            # Retourner les noms de profils triés
            return sorted([prof['name'] for prof in profiles.values()])
        except:
            return []

    def get_measurement_advice(self, measurements: List[Dict],
                               pdf_name: str,
                               profile_name: str = "ENTREPRENEUR GÉNÉRAL") -> str:
        """
        Obtient des conseils d'expert basés sur les mesures

        Args:
            measurements: Liste des mesures effectuées
            pdf_name: Nom du fichier PDF
            profile_name: Nom du profil expert à utiliser

        Returns:
            Conseils de l'expert IA
        """

        if not self.is_available():
            return "⚠️ Système expert non disponible. Assurez-vous d'avoir configuré votre clé API Claude."

        try:
            # Changer le profil actif
            self.expert_advisor.set_current_profile_by_name(profile_name)

            # Créer un résumé des mesures
            summary = self._create_measurements_summary(measurements, pdf_name)

            # Créer la question contextuelle
            question = f"""J'ai effectué des mesures sur un plan de construction PDF ({pdf_name}).

{summary}

En tant qu'expert, peux-tu:
1. Analyser ces mesures et identifier d'éventuelles incohérences
2. Suggérer des mesures supplémentaires importantes à effectuer
3. Donner des recommandations techniques basées sur ces quantités
4. Estimer si ces dimensions sont réalistes pour un projet de construction au Québec

Sois précis et technique dans tes recommandations."""

            # Obtenir la réponse de l'expert
            response = self.expert_advisor.obtenir_reponse(question, [])

            return response

        except Exception as e:
            return f"❌ Erreur lors de la consultation de l'expert: {str(e)}"

    def get_product_recommendations(self, measurement: Dict,
                                   profile_name: str = "ENTREPRENEUR GÉNÉRAL") -> str:
        """
        Obtient des recommandations de produits pour une mesure

        Args:
            measurement: Mesure pour laquelle obtenir des recommandations
            profile_name: Profil expert à utiliser

        Returns:
            Recommandations de produits
        """

        if not self.is_available():
            return "⚠️ Système expert non disponible."

        try:
            self.expert_advisor.set_current_profile_by_name(profile_name)

            # Créer la question
            measure_type = measurement.get('type', 'mesure')
            value = measurement.get('value', 0)
            unit = measurement.get('unit', '')

            question = f"""Pour un projet de construction au Québec, j'ai mesuré:
- Type: {measure_type}
- Valeur: {value} {unit}

Quels produits et matériaux recommandes-tu pour cette dimension?
Donne des options avec:
1. Produits recommandés (noms précis utilisés au Québec)
2. Quantités estimées
3. Prix approximatifs par unité (marché québécois 2025)
4. Alternatives possibles (économique vs haut de gamme)"""

            response = self.expert_advisor.obtenir_reponse(question, [])

            return response

        except Exception as e:
            return f"❌ Erreur: {str(e)}"

    def validate_calibration(self, calibration: Dict,
                            project_type: str = "Construction résidentielle") -> str:
        """
        Valide une calibration avec un expert

        Args:
            calibration: Dictionnaire de calibration
            project_type: Type de projet

        Returns:
            Validation et conseils
        """

        if not self.is_available():
            return "⚠️ Système expert non disponible."

        try:
            self.expert_advisor.set_current_profile_by_name("ENTREPRENEUR GÉNÉRAL")

            cal_value = calibration.get('value', 1.0)
            cal_unit = calibration.get('unit', 'pi')

            question = f"""J'ai calibré mon plan PDF avec la valeur suivante:
1 pixel = {cal_value:.4f} {cal_unit}

Pour un projet de type: {project_type}

Cette calibration te semble-t-elle réaliste?
- Est-ce cohérent avec les échelles standards des plans de construction au Québec?
- Y a-t-il des risques d'erreur avec cette échelle?
- Des recommandations pour valider cette calibration?"""

            response = self.expert_advisor.obtenir_reponse(question, [])

            return response

        except Exception as e:
            return f"❌ Erreur: {str(e)}"

    def analyze_project_totals(self, measurements: List[Dict],
                               totals: List[Dict],
                               profile_name: str = "ENTREPRENEUR GÉNÉRAL") -> str:
        """
        Analyse les totaux du projet avec un expert

        Args:
            measurements: Liste des mesures
            totals: Totaux calculés
            profile_name: Profil expert

        Returns:
            Analyse et recommandations
        """

        if not self.is_available():
            return "⚠️ Système expert non disponible."

        try:
            self.expert_advisor.set_current_profile_by_name(profile_name)

            # Créer le résumé
            total_items = len(measurements)
            total_cost = sum(
                float(t.get('Prix total', '0').replace('$', '').replace('N/D', '0').replace(',', ''))
                for t in totals
            )

            # Résumé par catégorie
            categories_summary = "\n".join([
                f"- {t.get('Catégorie', 'N/A')}: {t.get('Quantité', '0')} {t.get('Unité', '')} - {t.get('Prix total', 'N/D')}"
                for t in totals
            ])

            question = f"""Voici le résumé de mon projet de construction (mesures TAKEOFF AI):

STATISTIQUES:
- {total_items} mesures effectuées
- Total estimé: {total_cost:,.2f}$

DÉTAIL PAR CATÉGORIE:
{categories_summary}

En tant qu'expert, peux-tu:
1. Analyser si ces quantités et coûts sont cohérents
2. Identifier des postes manquants importants
3. Suggérer des optimisations possibles
4. Évaluer si le budget total est réaliste pour ce type de projet au Québec
5. Recommander des vérifications à faire avant de soumettre cette soumission"""

            response = self.expert_advisor.obtenir_reponse(question, [])

            return response

        except Exception as e:
            return f"❌ Erreur: {str(e)}"

    def get_specialized_advice(self, question: str, profile_name: str) -> str:
        """
        Obtient des conseils d'un expert spécialisé

        Args:
            question: Question à poser
            profile_name: Nom du profil expert

        Returns:
            Réponse de l'expert
        """

        if not self.is_available():
            return "⚠️ Système expert non disponible."

        try:
            self.expert_advisor.set_current_profile_by_name(profile_name)
            response = self.expert_advisor.obtenir_reponse(question, [])
            return response

        except Exception as e:
            return f"❌ Erreur: {str(e)}"

    def _create_measurements_summary(self, measurements: List[Dict], pdf_name: str) -> str:
        """Crée un résumé textuel des mesures"""

        if not measurements:
            return "Aucune mesure effectuée pour le moment."

        summary_parts = [f"PLAN: {pdf_name}", ""]

        # Grouper par type
        by_type = {}
        for m in measurements:
            m_type = m.get('type', 'autre')
            if m_type not in by_type:
                by_type[m_type] = []
            by_type[m_type].append(m)

        # Résumé par type
        type_names = {
            'distance': 'DISTANCES',
            'surface': 'SURFACES',
            'perimeter': 'PÉRIMÈTRES',
            'angle': 'ANGLES'
        }

        for m_type, items in by_type.items():
            type_name = type_names.get(m_type, m_type.upper())
            summary_parts.append(f"{type_name} ({len(items)}):")

            for item in items:
                label = item.get('label', 'Sans nom')
                value = item.get('value', 0)
                unit = item.get('unit', '')
                product = item.get('product', {})
                product_name = product.get('name', 'Aucun produit')

                summary_parts.append(
                    f"  - {label}: {value:.2f} {unit} → {product_name}"
                )

            summary_parts.append("")

        # Totaux
        total_surfaces = sum(
            m.get('value', 0) for m in measurements
            if m.get('type') == 'surface'
        )

        if total_surfaces > 0:
            summary_parts.append(f"TOTAL SURFACES: {total_surfaces:.2f} pi²")

        return "\n".join(summary_parts)

    def show_expert_panel(self):
        """Affiche le panneau de conseils expert dans l'interface"""

        if not self.is_available():
            st.warning("""
            ⚠️ **Système expert non disponible**

            Pour activer les conseils IA:
            1. Assurez-vous d'avoir configuré votre clé API Claude dans EXPERTS IA
            2. L'expert advisor sera automatiquement disponible
            """)
            return

        st.markdown("### 🧠 Conseils Expert IA")

        # Sélection du profil
        profiles = self.get_available_profiles()

        if not profiles:
            st.error("Aucun profil expert disponible")
            return

        # Trouver les profils les plus pertinents pour la construction
        recommended_profiles = [
            "ENTREPRENEUR GÉNÉRAL",
            "ARCHITECTE",
            "INGÉNIEUR STRUCTURE",
            "ÉLECTRICIEN",
            "PLOMBIER"
        ]

        # Filtre pour profils recommandés
        available_recommended = [p for p in recommended_profiles if p in profiles]
        other_profiles = [p for p in profiles if p not in recommended_profiles]

        selected_profile = st.selectbox(
            "Profil expert",
            options=available_recommended + other_profiles,
            format_func=lambda x: f"⭐ {x}" if x in available_recommended else x,
            key='takeoff_expert_profile'
        )

        # Types de conseils
        advice_type = st.radio(
            "Type de conseil",
            options=[
                'analyze_measurements',
                'product_recommendations',
                'validate_calibration',
                'analyze_totals',
                'custom_question'
            ],
            format_func=lambda x: {
                'analyze_measurements': '📐 Analyser mes mesures',
                'product_recommendations': '🛒 Recommandations produits',
                'validate_calibration': '🎯 Valider calibration',
                'analyze_totals': '💰 Analyser les totaux',
                'custom_question': '💬 Question personnalisée'
            }[x],
            key='takeoff_advice_type'
        )

        # Bouton pour obtenir les conseils
        if st.button("🚀 Obtenir les conseils", type="primary", use_container_width=True):
            with st.spinner(f"Consultation de {selected_profile}..."):

                measurements = st.session_state.get('takeoff_measurements', [])
                pdf_name = st.session_state.get('takeoff_pdf_name', 'plan.pdf')

                if advice_type == 'analyze_measurements':
                    if not measurements:
                        st.warning("Aucune mesure à analyser")
                    else:
                        advice = self.get_measurement_advice(measurements, pdf_name, selected_profile)
                        st.markdown("#### 📋 Analyse des mesures")
                        st.info(advice)

                elif advice_type == 'product_recommendations':
                    if not measurements:
                        st.warning("Ajoutez au moins une mesure")
                    else:
                        # Dernière mesure
                        last_measure = measurements[-1]
                        advice = self.get_product_recommendations(last_measure, selected_profile)
                        st.markdown(f"#### 🛒 Recommandations pour: {last_measure.get('label', 'Mesure')}")
                        st.info(advice)

                elif advice_type == 'validate_calibration':
                    calibration = st.session_state.get('takeoff_calibration', {'value': 1.0, 'unit': 'pi'})
                    advice = self.validate_calibration(calibration)
                    st.markdown("#### 🎯 Validation de la calibration")
                    st.info(advice)

                elif advice_type == 'analyze_totals':
                    if not measurements:
                        st.warning("Aucune mesure à analyser")
                    else:
                        from .measurement_tools import MeasurementTools
                        from .product_catalog import ProductCatalog

                        tools = st.session_state.get('takeoff_tools', MeasurementTools())
                        catalog = st.session_state.get('takeoff_catalog', ProductCatalog())

                        totals = tools.calculate_totals(measurements, catalog)
                        advice = self.analyze_project_totals(measurements, totals, selected_profile)

                        st.markdown("#### 💰 Analyse des totaux")
                        st.info(advice)

                elif advice_type == 'custom_question':
                    question = st.text_area(
                        "Votre question",
                        placeholder="Posez votre question à l'expert...",
                        key='custom_expert_question'
                    )

                    if question:
                        advice = self.get_specialized_advice(question, selected_profile)
                        st.markdown(f"#### 💬 {selected_profile}")
                        st.info(advice)
                    else:
                        st.warning("Entrez une question ci-dessus")
