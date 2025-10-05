"""
Interface TAKEOFF AI Phase 2 - Version Interactive Complète

Nouvelles fonctionnalités:
- Viewer PDF interactif avec canvas de dessin
- Calibration visuelle
- Accrochage intelligent aux lignes
- Conseils IA avec 65 profils experts
- Mesures par clics/tracés directs sur PDF
"""

import streamlit as st
import os
from datetime import datetime
from .interactive_pdf_viewer import InteractivePDFViewer
from .snap_system import SnapSystem
from .expert_advisor import TakeoffExpertAdvisor
from .measurement_tools import MeasurementTools
from .product_catalog import ProductCatalog


def show_takeoff_interface_v2():
    """Interface principale TAKEOFF AI Phase 2"""

    # Titre avec badge Phase 2
    st.markdown("""
    <div style="
        background: linear-gradient(145deg, #3B82F6 0%, #1F2937 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        position: relative;
    ">
        <div style="
            position: absolute;
            top: 10px;
            right: 20px;
            background: #10B981;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
        ">
            PHASE 2
        </div>
        <h2 style="margin: 0; color: white;">📐 TAKEOFF AI - Mode Interactif</h2>
        <p style="margin-top: 8px; margin-bottom: 0; opacity: 0.9;">
            Mesures directes sur PDF • Accrochage intelligent • Conseils IA experts
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialiser les outils
    if 'takeoff_tools' not in st.session_state:
        st.session_state.takeoff_tools = MeasurementTools()
        st.session_state.takeoff_catalog = ProductCatalog()
        st.session_state.takeoff_measurements = []
        st.session_state.takeoff_current_pdf = None
        st.session_state.takeoff_pdf_name = None
        st.session_state.takeoff_calibration = {'value': 1.0, 'unit': 'pi'}
        st.session_state.takeoff_selected_tool = 'distance'
        st.session_state.takeoff_snap_enabled = True

    # Initialiser les nouveaux outils Phase 2
    if 'pdf_viewer' not in st.session_state:
        st.session_state.pdf_viewer = InteractivePDFViewer()

    if 'snap_system' not in st.session_state:
        st.session_state.snap_system = SnapSystem(snap_threshold=15)

    if 'expert_advisor' not in st.session_state:
        st.session_state.expert_advisor_takeoff = TakeoffExpertAdvisor()

    # Mode d'affichage
    display_mode = st.sidebar.radio(
        "🎨 Mode d'affichage",
        options=['interactive', 'classic'],
        format_func=lambda x: {
            'interactive': '🖱️ Interactif (Phase 2)',
            'classic': '📝 Classique (Phase 1)'
        }[x],
        key='takeoff_display_mode',
        help="Mode interactif: dessinez sur le PDF. Mode classique: formulaires manuels"
    )

    # Layout principal
    if display_mode == 'interactive':
        show_interactive_mode()
    else:
        # Importer et afficher le mode classique
        from .takeoff_interface import show_takeoff_interface
        show_takeoff_interface()


def show_interactive_mode():
    """Mode interactif Phase 2 complet"""

    # Layout en colonnes
    col1, col2, col3 = st.columns([2, 5, 3])

    # ===== COLONNE 1: Fichier PDF et Outils =====
    with col1:
        st.subheader("📂 Fichier PDF")

        # Upload PDF
        uploaded_pdf = st.file_uploader(
            "Charger un plan",
            type=['pdf'],
            key='takeoff_pdf_upload_v2',
            help="PDF de plan de construction"
        )

        if uploaded_pdf:
            # Sauvegarder
            temp_dir = "temp/takeoff"
            os.makedirs(temp_dir, exist_ok=True)
            temp_pdf_path = os.path.join(temp_dir, uploaded_pdf.name)

            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_pdf.getbuffer())

            st.session_state.takeoff_current_pdf = temp_pdf_path
            st.session_state.takeoff_pdf_name = uploaded_pdf.name

            st.success(f"✅ {uploaded_pdf.name}")
            file_size = len(uploaded_pdf.getvalue()) / 1024
            st.caption(f"Taille: {file_size:.1f} KB")

            st.divider()

            # === OUTILS DE MESURE ===
            st.subheader("🛠️ Outils de mesure")

            tool_options = {
                'distance': '📏 Distance',
                'surface': '⬜ Surface',
                'perimeter': '🔲 Périmètre',
                'angle': '📐 Angle',
                'calibration': '🎯 Calibration',
                'point': '📍 Point de référence'
            }

            selected_tool = st.radio(
                "Type de mesure",
                options=list(tool_options.keys()),
                format_func=lambda x: tool_options[x],
                key='takeoff_tool_selector_v2'
            )

            st.session_state.takeoff_selected_tool = selected_tool

            st.divider()

            # === ACCROCHAGE INTELLIGENT ===
            st.subheader("🧲 Accrochage")

            snap_enabled = st.checkbox(
                "Activer l'accrochage",
                value=st.session_state.takeoff_snap_enabled,
                key='snap_enabled_checkbox',
                help="Accroche automatiquement aux lignes, points, intersections"
            )

            st.session_state.takeoff_snap_enabled = snap_enabled

            if snap_enabled:
                snap_threshold = st.slider(
                    "Seuil (pixels)",
                    min_value=5,
                    max_value=30,
                    value=15,
                    key='snap_threshold_slider'
                )

                st.session_state.snap_system.snap_threshold = snap_threshold

                # Modes d'accrochage
                st.caption("**Modes actifs:**")

                snap_modes = []

                if st.checkbox("Extrémités", value=True, key='snap_endpoints'):
                    snap_modes.append('endpoints')

                if st.checkbox("Milieux", value=True, key='snap_midpoints'):
                    snap_modes.append('midpoints')

                if st.checkbox("Intersections", value=True, key='snap_intersections'):
                    snap_modes.append('intersections')

                if st.checkbox("Perpendiculaire", value=True, key='snap_perpendicular'):
                    snap_modes.append('perpendicular')

                if st.checkbox("Orthogonal", value=True, key='snap_orthogonal'):
                    snap_modes.append('orthogonal')

                st.session_state.snap_system.enable_snap_modes(snap_modes)

            st.divider()

            # === CALIBRATION ===
            st.subheader("📊 Calibration")

            col_cal1, col_cal2 = st.columns(2)

            with col_cal1:
                cal_value = st.number_input(
                    "Facteur",
                    value=st.session_state.takeoff_calibration['value'],
                    min_value=0.001,
                    step=0.1,
                    format="%.3f",
                    key='takeoff_cal_value_v2'
                )

            with col_cal2:
                cal_unit = st.selectbox(
                    "Unité",
                    options=['pi', 'pi²', 'm', 'm²', 'ft', 'ft²'],
                    index=0,
                    key='takeoff_cal_unit_v2'
                )

            st.session_state.takeoff_calibration = {
                'value': cal_value,
                'unit': cal_unit
            }

            st.caption(f"1 pixel = {cal_value:.3f} {cal_unit}")

            # Bouton valider calibration avec expert
            if st.button("🔍 Valider avec expert IA", use_container_width=True):
                advisor = st.session_state.expert_advisor_takeoff
                if advisor.is_available():
                    with st.spinner("Validation..."):
                        validation = advisor.validate_calibration(
                            st.session_state.takeoff_calibration
                        )
                        st.info(validation)
                else:
                    st.warning("Expert IA non disponible")

            st.divider()

            # === CATALOGUE ===
            st.subheader("📦 Catalogue")

            categories = st.session_state.takeoff_catalog.get_categories()

            if categories:
                selected_category = st.selectbox(
                    "Catégorie",
                    options=categories,
                    key='takeoff_category_select_v2'
                )

                products = st.session_state.takeoff_catalog.get_products_by_category(selected_category)

                if products:
                    product_names = list(products.keys())
                    selected_product = st.selectbox(
                        "Produit",
                        options=product_names,
                        key='takeoff_product_select_v2'
                    )

                    product_data = products[selected_product]

                    st.caption(f"**Prix:** {product_data['price']:.2f}$ / {product_data['price_unit']}")
                    st.caption(f"**Dimensions:** {product_data['dimensions']}")

                    st.session_state.takeoff_selected_product = {
                        'name': selected_product,
                        'category': selected_category,
                        'price': product_data['price'],
                        'unit': product_data['price_unit']
                    }

        else:
            st.info("👆 Chargez un fichier PDF pour commencer")

    # ===== COLONNE 2: Visualisation PDF Interactive =====
    with col2:
        st.subheader("📄 Plan interactif")

        if st.session_state.takeoff_current_pdf:
            # Afficher le viewer interactif
            viewer = st.session_state.pdf_viewer
            viewer.render_interactive(
                st.session_state.takeoff_current_pdf,
                st.session_state.takeoff_selected_tool
            )

            # Dialogue de calibration si nécessaire
            if 'calibration_pending' in st.session_state:
                viewer.render_calibration_dialog()

        else:
            # Placeholder
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #F5F8FF 0%, #DBEAFE 100%);
                padding: 120px 20px;
                border-radius: 12px;
                text-align: center;
                border: 2px dashed #3B82F6;
            ">
                <p style="font-size: 64px; margin: 0;">📋</p>
                <p style="color: #6B7280; margin-top: 24px; font-size: 18px;">
                    Chargez un plan PDF pour utiliser le mode interactif
                </p>
                <p style="color: #9CA3AF; margin-top: 12px;">
                    Dessinez directement sur le PDF pour mesurer
                </p>
            </div>
            """, unsafe_allow_html=True)

    # ===== COLONNE 3: Mesures et Expert IA =====
    with col3:
        # Tabs pour organiser
        tab1, tab2, tab3 = st.tabs(["📊 Mesures", "🧠 Expert IA", "⚙️ Options"])

        with tab1:
            show_measurements_panel()

        with tab2:
            show_expert_panel()

        with tab3:
            show_options_panel()


def show_measurements_panel():
    """Panneau des mesures effectuées"""

    st.subheader("📊 Mesures")

    measurements = st.session_state.takeoff_measurements

    if measurements:
        st.caption(f"**Total: {len(measurements)} mesures**")

        for i, measure in enumerate(measurements):
            with st.expander(
                f"{get_measure_icon(measure['type'])} {measure['label']}",
                expanded=(i == len(measurements) - 1)
            ):
                st.write(f"**Type:** {measure['type']}")
                st.write(f"**Valeur:** {measure['value']:.2f} {measure['unit']}")

                if measure.get('product'):
                    product = measure['product']
                    st.write(f"**Produit:** {product.get('name', 'N/A')}")

                    if product.get('price'):
                        cost = measure['value'] * product['price']
                        st.write(f"**Coût:** {cost:.2f}$")

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("🗑️", key=f"delete_measure_v2_{i}", use_container_width=True):
                        st.session_state.takeoff_measurements.pop(i)
                        st.rerun()

                with col_b:
                    if st.button("📝", key=f"edit_measure_v2_{i}", use_container_width=True):
                        st.session_state.editing_measure = i

        st.divider()

        # Totaux
        st.subheader("💰 Totaux")

        totals = st.session_state.takeoff_tools.calculate_totals(
            measurements,
            st.session_state.takeoff_catalog
        )

        if totals:
            import pandas as pd
            df_totals = pd.DataFrame(totals)
            st.dataframe(df_totals, use_container_width=True, hide_index=True)

            grand_total = sum(
                float(row['Prix total'].replace('$', '').replace('N/D', '0'))
                for row in totals
            )

            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #DCFCE7 0%, #FFFFFF 100%);
                padding: 16px;
                border-radius: 8px;
                border-left: 4px solid #22C55E;
                margin-top: 12px;
            ">
                <p style="margin: 0; font-size: 14px; color: #6B7280;">Total estimé</p>
                <p style="margin: 0; font-size: 24px; font-weight: 700; color: #1F2937;">
                    {grand_total:,.2f}$
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Actions
        if st.button("📤 Exporter vers Soumission", use_container_width=True, type="primary"):
            from .integration_bridge import export_to_soumission_experts

            result = export_to_soumission_experts(
                measurements,
                st.session_state.takeoff_catalog,
                st.session_state.takeoff_pdf_name
            )

            if result['success']:
                st.success("✅ Exporté vers Soumissions!")
                st.info("👉 Allez dans l'onglet 'Soumissions' pour finaliser")
            else:
                st.error(f"❌ {result.get('error')}")

    else:
        st.info("Aucune mesure pour le moment")


def show_expert_panel():
    """Panneau conseils expert IA"""

    advisor = st.session_state.get('expert_advisor_takeoff')

    if advisor:
        advisor.show_expert_panel()
    else:
        st.warning("Expert IA non disponible")


def show_options_panel():
    """Panneau des options"""

    st.subheader("⚙️ Options")

    # Paramètres d'affichage
    st.write("**Affichage:**")

    show_grid = st.checkbox("Afficher grille", value=False, key='show_grid_option')
    show_rulers = st.checkbox("Afficher règles", value=False, key='show_rulers_option')
    show_dimensions = st.checkbox("Dimensions auto", value=True, key='show_dimensions_option')

    st.divider()

    # Paramètres de dessin
    st.write("**Dessin:**")

    line_width = st.slider("Épaisseur trait", 1, 10, 3, key='line_width_option')
    line_opacity = st.slider("Opacité", 0.1, 1.0, 0.8, step=0.1, key='line_opacity_option')

    st.divider()

    # Export
    st.write("**Export:**")

    if st.button("📥 Exporter CSV", use_container_width=True):
        import pandas as pd
        import io

        measurements = st.session_state.takeoff_measurements

        if measurements:
            df_export = pd.DataFrame(measurements)
            csv_buffer = io.StringIO()
            df_export.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="💾 Télécharger CSV",
                data=csv_data,
                file_name=f"takeoff_measures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("Aucune mesure à exporter")

    # Réinitialisation
    st.divider()

    if st.button("🗑️ Tout effacer", use_container_width=True):
        if st.session_state.get('confirm_delete_all_v2'):
            st.session_state.takeoff_measurements = []
            st.session_state.confirm_delete_all_v2 = False
            st.success("✅ Tout effacé")
            st.rerun()
        else:
            st.session_state.confirm_delete_all_v2 = True
            st.warning("⚠️ Cliquez à nouveau pour confirmer")


def get_measure_icon(measure_type: str) -> str:
    """Retourne l'icône selon le type de mesure"""
    icons = {
        'distance': '📏',
        'surface': '⬜',
        'perimeter': '🔲',
        'angle': '📐',
        'point': '📍'
    }
    return icons.get(measure_type, '📌')
