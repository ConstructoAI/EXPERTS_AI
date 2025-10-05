"""
Interface d'intégration TAKEOFF AI dans EXPERTS IA

Cette interface permet de:
- Charger et visualiser des plans PDF
- Effectuer des mesures (distance, surface, périmètre, angle)
- Associer des produits aux mesures
- Exporter les données vers les soumissions EXPERTS IA
"""

import streamlit as st
import os
import base64
from datetime import datetime
from .measurement_tools import MeasurementTools
from .product_catalog import ProductCatalog
from .takeoff_db import (
    init_takeoff_db, save_project, save_all_measurements,
    get_all_projects, load_project, delete_project,
    get_project_stats, search_projects, update_project
)
from .simple_reactive_viewer import render_pdf_viewer, show_calibration_dialog

def show_takeoff_interface():
    """Interface principale TAKEOFF AI intégrée"""

    # Initialiser la base de données
    init_takeoff_db()

    # Titre de la section
    st.markdown("""
    <div style="
        background: linear-gradient(145deg, #3B82F6 0%, #1F2937 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    ">
        <h2 style="margin: 0; color: white;">📐 Métré PDF - Mesures et Quantitatif</h2>
        <p style="margin-top: 8px; margin-bottom: 0; opacity: 0.9;">
            Mesurez vos plans PDF et exportez vers soumissions
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialiser les outils TAKEOFF dans session state
    if 'takeoff_tools' not in st.session_state:
        st.session_state.takeoff_tools = MeasurementTools()
        st.session_state.takeoff_catalog = ProductCatalog()
        st.session_state.takeoff_measurements = []
        st.session_state.takeoff_current_pdf = None
        st.session_state.takeoff_pdf_name = None
        st.session_state.takeoff_calibration = {'value': 1.0, 'unit': 'pi'}
        st.session_state.takeoff_selected_tool = 'distance'
        st.session_state.takeoff_temp_points = []
        st.session_state.takeoff_current_page = 0
        st.session_state.takeoff_total_pages = 0
        st.session_state.takeoff_zoom = 1.5  # Zoom par défaut
        st.session_state.takeoff_current_project_id = None  # ID du projet en cours

    # Tabs pour séparer nouveau métré et projets sauvegardés
    tab1, tab2 = st.tabs(["📐 Nouveau Métré", "📁 Projets Sauvegardés"])

    with tab1:
        show_new_takeoff()

    with tab2:
        show_saved_projects()


def show_new_takeoff():
    """Interface pour créer un nouveau métré"""

    # ===== PANNEAU DE CONTRÔLE COMPLET AU-DESSUS DU PDF =====
    st.markdown("### 🎛️ Panneau de Contrôle")

    # Ligne 1: Chargement du fichier PDF
    st.markdown("#### 📂 1. Chargement du Plan")
    col_upload, col_info = st.columns([3, 2])

    with col_upload:
        uploaded_pdf = st.file_uploader(
            "Sélectionnez votre plan PDF",
            type=['pdf'],
            key='takeoff_pdf_upload',
            help="Formats supportés: PDF | Maximum: 200 MB"
        )

        if uploaded_pdf:
            # Sauvegarder temporairement
            temp_dir = "temp/takeoff"
            os.makedirs(temp_dir, exist_ok=True)
            temp_pdf_path = os.path.join(temp_dir, uploaded_pdf.name)

            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_pdf.getbuffer())

            st.session_state.takeoff_current_pdf = temp_pdf_path
            st.session_state.takeoff_pdf_name = uploaded_pdf.name

            # Compter le nombre de pages
            try:
                import fitz  # PyMuPDF
                pdf_doc = fitz.open(temp_pdf_path)
                st.session_state.takeoff_total_pages = pdf_doc.page_count
                pdf_doc.close()
            except:
                st.session_state.takeoff_total_pages = 1

            # Reset à la première page lors d'un nouveau chargement
            st.session_state.takeoff_current_page = 0

    with col_info:
        if st.session_state.takeoff_current_pdf:
            st.success("✅ Plan chargé")
            st.caption(f"📄 **{st.session_state.takeoff_pdf_name}**")
            st.caption(f"📑 **{st.session_state.takeoff_total_pages}** page(s)")
        else:
            st.info("Aucun plan chargé")

    st.divider()

    # Ligne 2: Outils de mesure + Calibration
    st.markdown("#### 🛠️ 2. Outils et Calibration")
    col_tools, col_calib = st.columns([3, 2])

    with col_tools:
        st.markdown("**Sélection de l'outil**")

        tool_options = {
            'distance': '📏 Distance',
            'surface': '⬜ Surface',
            'perimeter': '🔲 Périmètre',
            'angle': '📐 Angle',
            'calibration': '🎯 Calibration'
        }

        selected_tool = st.selectbox(
            "Type de mesure",
            options=list(tool_options.keys()),
            format_func=lambda x: tool_options[x],
            key='takeoff_tool_selector',
            label_visibility="collapsed"
        )

        st.session_state.takeoff_selected_tool = selected_tool

        # Description de l'outil sélectionné
        tool_descriptions = {
            'distance': "Mesure la distance entre deux points",
            'surface': "Calcule l'aire d'une zone polygonale",
            'perimeter': "Mesure le périmètre d'une zone",
            'angle': "Mesure l'angle entre deux lignes",
            'calibration': "Définir l'échelle du plan"
        }
        st.caption(f"ℹ️ {tool_descriptions.get(selected_tool, '')}")

    with col_calib:
        st.markdown("**Calibration & Unités**")

        # Afficher la calibration actuelle (lecture seule si calibrée)
        current_cal = st.session_state.takeoff_calibration

        st.caption(f"**Facteur actuel:** {current_cal['value']:.6f} {current_cal['unit']}/pixel")
        st.caption("💡 Utilisez l'outil 🎯 Calibration pour calibrer le plan")

    st.divider()

    # Ligne 3: Catalogue de produits + Gestion du catalogue
    st.markdown("#### 📦 3. Catalogue de Produits")
    col_catalog, col_catalog_btn = st.columns([4, 1])

    with col_catalog:
        categories = st.session_state.takeoff_catalog.get_categories()

        if categories:
            col_cat, col_prod = st.columns(2)

            with col_cat:
                selected_category = st.selectbox(
                    "Catégorie",
                    options=categories,
                    key='takeoff_category_select'
                )

            with col_prod:
                products = st.session_state.takeoff_catalog.get_products_by_category(selected_category)

                if products:
                    product_names = list(products.keys())
                    selected_product = st.selectbox(
                        "Produit",
                        options=product_names,
                        key='takeoff_product_select'
                    )

                    product_data = products[selected_product]

                    # Stocker le produit sélectionné
                    st.session_state.takeoff_selected_product = {
                        'name': selected_product,
                        'category': selected_category,
                        'price': product_data['price'],
                        'unit': product_data['price_unit']
                    }

                    # Afficher le prix
                    if product_data.get('price'):
                        st.caption(f"💰 {product_data['price']:.2f}$ / {product_data.get('price_unit', 'u')}")
                else:
                    st.info("Aucun produit dans cette catégorie")
        else:
            st.info("📋 Catalogue vide - Cliquez sur 'Gérer' pour ajouter des produits")

    with col_catalog_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔧 Gérer Catalogue", use_container_width=True, key="btn_manage_catalog"):
            st.session_state.show_catalog_manager = True
            st.rerun()

    st.divider()

    # Ligne 4: Résumé des mesures
    st.markdown("#### 📊 4. Résumé des Mesures")
    col_summary, col_actions = st.columns([3, 2])

    with col_summary:
        measurements = st.session_state.takeoff_measurements
        if measurements:
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("📏 Mesures", len(measurements))
            with col_m2:
                # Calculer total estimé
                totals = st.session_state.takeoff_tools.calculate_totals(
                    measurements,
                    st.session_state.takeoff_catalog
                )
                if totals:
                    grand_total = sum(
                        float(row['Prix total'].replace('$', '').replace('N/D', '0'))
                        for row in totals
                    )
                    st.metric("💰 Total", f"{grand_total:,.2f}$")
                else:
                    st.metric("💰 Total", "0.00$")
            with col_m3:
                # Dernière mesure
                if measurements:
                    last_measure = measurements[-1]
                    st.metric("🔄 Dernière", f"{last_measure['value']:.1f} {last_measure['unit']}")
        else:
            st.info("Aucune mesure effectuée pour le moment")

    with col_actions:
        st.markdown("**Actions rapides**")
        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            if st.button("💾 Sauvegarder", use_container_width=True, disabled=len(measurements)==0):
                st.session_state.show_save_dialog = True

        with col_a2:
            if st.button("📥 Export CSV", use_container_width=True, disabled=len(measurements)==0):
                import pandas as pd
                import io

                df_export = pd.DataFrame(measurements)
                csv_buffer = io.StringIO()
                df_export.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_data = csv_buffer.getvalue()

                st.download_button(
                    label="💾 Télécharger",
                    data=csv_data,
                    file_name=f"takeoff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with col_a3:
            if st.button("🗑️ Effacer", use_container_width=True, disabled=len(measurements)==0):
                if st.session_state.get('confirm_delete_all'):
                    st.session_state.takeoff_measurements = []
                    st.session_state.confirm_delete_all = False
                    st.rerun()
                else:
                    st.session_state.confirm_delete_all = True

    # ===== DIALOGUE DE SAUVEGARDE =====
    if st.session_state.get('show_save_dialog'):
        st.divider()
        with st.expander("💾 Sauvegarder le projet de métré", expanded=True):
            with st.form("save_project_form"):
                st.markdown("**Enregistrer ce projet pour le retrouver plus tard**")

                nom_projet = st.text_input(
                    "Nom du projet *",
                    value=st.session_state.takeoff_pdf_name or "",
                    help="Nom pour identifier ce projet",
                    key="input_nom_projet"
                )

                client_nom = st.text_input(
                    "Client (optionnel)",
                    help="Nom du client associé à ce projet",
                    key="input_client_nom"
                )

                notes = st.text_area(
                    "Notes (optionnel)",
                    help="Notes ou commentaires sur ce projet",
                    key="input_notes"
                )

                col_save, col_cancel = st.columns(2)
                with col_save:
                    submit_save = st.form_submit_button("✅ Sauvegarder", use_container_width=True)
                with col_cancel:
                    cancel_save = st.form_submit_button("❌ Annuler", use_container_width=True)

                if submit_save and nom_projet:
                    try:
                        # Sauvegarder le projet
                        if st.session_state.get('takeoff_current_project_id'):
                            # Mise à jour projet existant
                            project_id = st.session_state.takeoff_current_project_id
                            update_project(
                                project_id,
                                nom_projet=nom_projet,
                                client_nom=client_nom,
                                notes=notes
                            )
                            save_all_measurements(project_id, st.session_state.takeoff_measurements)
                            st.success(f"✅ Projet '{nom_projet}' mis à jour avec succès!")
                        else:
                            # Nouveau projet
                            project_id = save_project(
                                nom_projet=nom_projet,
                                client_nom=client_nom,
                                pdf_nom=st.session_state.takeoff_pdf_name,
                                pdf_path=st.session_state.takeoff_current_pdf,
                                calibration=st.session_state.takeoff_calibration,
                                notes=notes
                            )
                            save_all_measurements(project_id, st.session_state.takeoff_measurements)
                            st.session_state.takeoff_current_project_id = project_id
                            st.success(f"✅ Projet '{nom_projet}' sauvegardé avec {len(st.session_state.takeoff_measurements)} mesure(s)!")

                        st.session_state.show_save_dialog = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la sauvegarde: {str(e)}")

                if cancel_save:
                    st.session_state.show_save_dialog = False
                    st.rerun()

    # ===== SECTION AJOUT ET GESTION DES MESURES =====
    if st.session_state.takeoff_current_pdf:
        st.divider()
        st.markdown("#### ➕ 5. Ajout et Gestion des Mesures")

        col_form, col_list = st.columns([2, 3])

        with col_form:
            st.markdown("**Saisie manuelle d'une mesure**")

            with st.form("manual_measurement_form", clear_on_submit=True):
                measure_label = st.text_input("Description", placeholder="Ex: Mur extérieur nord", help="Nom descriptif de la mesure")

                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    measure_value = st.number_input(
                        "Valeur",
                        min_value=0.0,
                        step=0.1,
                        value=0.0,
                        help="Valeur numérique"
                    )

                with col_m2:
                    measure_unit = st.selectbox(
                        "Unité",
                        options=['pi', 'pi²', 'm', 'm²', 'ft', 'ft²'],
                        help="Unité de mesure"
                    )

                with col_m3:
                    measure_type = st.selectbox(
                        "Type",
                        options=['distance', 'surface', 'perimeter', 'angle'],
                        format_func=lambda x: {
                            'distance': 'Distance',
                            'surface': 'Surface',
                            'perimeter': 'Périmètre',
                            'angle': 'Angle'
                        }[x],
                        help="Type de mesure"
                    )

                # Associer un produit (optionnel)
                if st.session_state.get('takeoff_selected_product'):
                    prod = st.session_state.takeoff_selected_product
                    st.caption(f"🏷️ Produit associé: **{prod['name']}** ({prod['price']:.2f}$ / {prod['unit']})")

                submit_measure = st.form_submit_button("✅ Ajouter la Mesure", use_container_width=True, type="primary")

                if submit_measure and measure_value > 0:
                    # Créer la mesure
                    new_measure = {
                        'label': measure_label or f"Mesure #{len(st.session_state.takeoff_measurements) + 1}",
                        'type': measure_type,
                        'value': measure_value,
                        'unit': measure_unit,
                        'product': st.session_state.get('takeoff_selected_product', {}),
                        'timestamp': datetime.now().isoformat()
                    }

                    st.session_state.takeoff_measurements.append(new_measure)
                    st.success(f"✅ Mesure '{new_measure['label']}' ajoutée!")
                    st.rerun()
                elif submit_measure:
                    st.warning("⚠️ La valeur doit être supérieure à 0")

        with col_list:
            st.markdown("**Liste détaillée**")

            measurements = st.session_state.takeoff_measurements

            if measurements:
                # Conteneur scrollable pour la liste
                st.caption(f"📋 {len(measurements)} mesure(s) enregistrée(s)")

                # Afficher toutes les mesures dans des expanders
                for i, measure in enumerate(measurements):
                    with st.expander(
                        f"{i+1}. {measure['label']} - {measure['value']:.2f} {measure['unit']}",
                        expanded=(i == len(measurements) - 1 and len(measurements) <= 3)
                    ):
                        col_info, col_del = st.columns([4, 1])

                        with col_info:
                            st.write(f"**Type:** {measure['type'].capitalize()}")
                            st.write(f"**Valeur:** {measure['value']:.2f} {measure['unit']}")

                            if measure.get('product') and measure['product'].get('name'):
                                product = measure['product']
                                st.write(f"**Produit:** {product.get('name', 'N/A')}")

                                # Calculer le coût
                                if product.get('price'):
                                    cost = measure['value'] * product['price']
                                    st.write(f"**Coût:** {cost:.2f}$")
                            else:
                                st.caption("_Aucun produit associé_")

                        with col_del:
                            if st.button("🗑️", key=f"delete_measure_{i}", help="Supprimer cette mesure"):
                                st.session_state.takeoff_measurements.pop(i)
                                st.rerun()

                st.divider()

                # Export vers Soumission EXPERTS IA
                if st.button("📤 Exporter vers Soumission", use_container_width=True, type="primary", key="export_to_submission"):
                    # Importer le module bridge
                    from .integration_bridge import export_to_soumission_experts

                    try:
                        result = export_to_soumission_experts(
                            measurements,
                            st.session_state.takeoff_catalog,
                            st.session_state.takeoff_pdf_name
                        )

                        if result['success']:
                            st.success("✅ Données exportées vers Soumissions!")
                            st.info("👉 Allez dans l'onglet 'Soumissions' pour finaliser")

                            # Afficher le résumé
                            st.caption(f"📊 {result['nb_items']} items exportés | {result['nb_categories']} catégories | {result['total_estime']:,.2f}$")
                        else:
                            st.error(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")

                    except ImportError:
                        st.warning("⚠️ Module d'export disponible en Phase 2")

            else:
                st.info("Aucune mesure pour le moment")

                # Message d'encouragement
                st.markdown("""
                <div style="
                    background: #F8FAFF;
                    padding: 16px;
                    border-radius: 8px;
                    border: 1px solid #DBEAFE;
                    margin-top: 16px;
                ">
                    <p style="margin: 0; font-size: 14px; color: #6B7280; text-align: center;">
                        👆 Ajoutez des mesures pour commencer
                    </p>
                </div>
                """, unsafe_allow_html=True)

    # ===== VISUALISATION PDF EN GRAND (Pleine largeur) =====
    st.divider()
    st.markdown("### 📄 Visualisation du Plan")

    if st.session_state.takeoff_current_pdf:
        # Navigation de pages (style TAKEOFF AI original)
        if st.session_state.takeoff_total_pages > 1:
            col_prev, col_page, col_next, col_info = st.columns([1, 3, 1, 3])

            # Définir les callbacks pour les boutons
            def go_prev():
                if st.session_state.takeoff_current_page > 0:
                    st.session_state.takeoff_current_page -= 1

            def go_next():
                if st.session_state.takeoff_current_page < st.session_state.takeoff_total_pages - 1:
                    st.session_state.takeoff_current_page += 1

            def on_page_change():
                # Le selectbox met à jour via sa clé directement
                pass

            with col_prev:
                st.button(
                    "◀ Précédent",
                    disabled=st.session_state.takeoff_current_page == 0,
                    key="prev_page_btn",
                    use_container_width=True,
                    on_click=go_prev
                )

            with col_page:
                # Utiliser un selectbox avec on_change
                page_options = list(range(1, st.session_state.takeoff_total_pages + 1))

                # Calculer l'index pour le selectbox
                current_index = st.session_state.takeoff_current_page

                selected_page = st.selectbox(
                    "Page",
                    options=page_options,
                    index=current_index,
                    label_visibility="collapsed",
                    key="page_selector_widget"
                )

                # Mettre à jour la page courante basée sur la sélection
                st.session_state.takeoff_current_page = selected_page - 1

            with col_next:
                st.button(
                    "Suivant ▶",
                    disabled=st.session_state.takeoff_current_page >= st.session_state.takeoff_total_pages - 1,
                    key="next_page_btn",
                    use_container_width=True,
                    on_click=go_next
                )

            with col_info:
                st.info(f"📄 Page {st.session_state.takeoff_current_page + 1}/{st.session_state.takeoff_total_pages}")

        # ===== CONTRÔLES DE ZOOM =====
        st.markdown("#### 🔍 Zoom et Affichage")

        col_zoom, col_info_zoom = st.columns([3, 1])

        with col_zoom:
            # Utiliser une clé unique pour le slider
            new_zoom = st.slider(
                "Niveau de zoom",
                min_value=0.5,
                max_value=3.0,
                value=st.session_state.takeoff_zoom,
                step=0.1,
                key="takeoff_zoom_slider",
                help="Ajustez le niveau de zoom pour voir les détails du plan"
            )
            # Mettre à jour seulement si changé
            if new_zoom != st.session_state.takeoff_zoom:
                st.session_state.takeoff_zoom = new_zoom

        with col_info_zoom:
            # Bouton reset zoom
            if st.button("🔄 Reset Zoom", use_container_width=True):
                st.session_state.takeoff_zoom = 1.5
                st.rerun()

        # Afficher le pourcentage de zoom
        zoom_percentage = int(st.session_state.takeoff_zoom * 100)
        st.caption(f"📊 Zoom actuel: **{zoom_percentage}%**")

        # Afficher le dialogue de calibration EN PREMIER (avant le viewer)
        show_calibration_dialog()

        # Afficher le viewer interactif avec gestion des clics
        render_pdf_viewer(
            pdf_path=st.session_state.takeoff_current_pdf,
            current_page=st.session_state.takeoff_current_page,
            measurements=st.session_state.takeoff_measurements,
            selected_tool=st.session_state.takeoff_selected_tool,
            calibration=st.session_state.takeoff_calibration,
            zoom=st.session_state.takeoff_zoom
        )

    else:
        st.info("Aucun PDF chargé")

        # Image placeholder
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #F5F8FF 0%, #DBEAFE 100%);
            padding: 80px 20px;
            border-radius: 12px;
            text-align: center;
            border: 2px dashed #3B82F6;
        ">
            <p style="font-size: 48px; margin: 0;">📋</p>
            <p style="color: #6B7280; margin-top: 16px;">
                Chargez un plan PDF pour commencer vos mesures
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Gérer le catalogue (modal)
    if st.session_state.get('show_catalog_manager', False):
        show_catalog_manager()


def show_saved_projects():
    """Interface pour afficher et gérer les projets sauvegardés"""

    st.markdown("### 📁 Mes Projets de Métré")

    # Statistiques globales
    stats = get_project_stats()
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("📊 Total Projets", stats['total_projects'])
    with col_s2:
        st.metric("📏 Total Mesures", stats['total_measurements'])
    with col_s3:
        st.metric("💰 Montant Total", f"{stats['total_amount']:,.2f}$")
    with col_s4:
        st.metric("🔄 En cours", stats['projects_en_cours'])

    st.divider()

    # Recherche et filtres
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_term = st.text_input("🔍 Rechercher par nom ou client", key="search_projects")
    with col_filter:
        statut_filter = st.selectbox(
            "Statut",
            options=["Tous", "en_cours", "termine", "archive"],
            key="filter_statut"
        )

    st.divider()

    # Récupérer les projets
    if search_term:
        projects = search_projects(search_term)
    elif statut_filter != "Tous":
        projects = get_all_projects(statut=statut_filter)
    else:
        projects = get_all_projects()

    if not projects:
        st.info("📂 Aucun projet sauvegardé. Créez votre premier métré dans l'onglet 'Nouveau Métré'!")
        return

    # Afficher les projets
    st.markdown(f"**{len(projects)} projet(s) trouvé(s)**")

    for proj in projects:
        project_id, nom_projet, client_nom, pdf_nom, total_mesures, total_montant, date_creation, date_modification, statut = proj

        # Badge de statut
        statut_colors = {
            'en_cours': '🟡',
            'termine': '🟢',
            'archive': '⚪'
        }
        statut_badge = statut_colors.get(statut, '🔵')

        with st.expander(f"{statut_badge} **{nom_projet}** - {total_mesures} mesure(s) - {total_montant:,.2f}$"):
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                if client_nom:
                    st.markdown(f"**Client:** {client_nom}")
                if pdf_nom:
                    st.markdown(f"**Plan PDF:** {pdf_nom}")
                st.caption(f"📅 Créé: {date_creation} | Modifié: {date_modification}")
                st.caption(f"📊 {total_mesures} mesure(s) | 💰 {total_montant:,.2f}$")

            with col_actions:
                if st.button("📂 Charger", key=f"load_{project_id}", use_container_width=True):
                    try:
                        data = load_project(project_id)
                        if data:
                            # Charger les données dans session_state
                            st.session_state.takeoff_measurements = data['measurements']
                            st.session_state.takeoff_current_project_id = project_id
                            if data['project'].get('calibration'):
                                st.session_state.takeoff_calibration = data['project']['calibration']
                            if data['project'].get('pdf_nom'):
                                st.session_state.takeoff_pdf_name = data['project']['pdf_nom']

                            st.success(f"✅ Projet '{nom_projet}' chargé avec {len(data['measurements'])} mesure(s)!")
                            st.info("👉 Retournez à l'onglet 'Nouveau Métré' pour continuer")
                    except Exception as e:
                        st.error(f"❌ Erreur lors du chargement: {str(e)}")

                if st.button("🗑️ Supprimer", key=f"del_{project_id}", use_container_width=True):
                    if st.session_state.get(f'confirm_del_{project_id}'):
                        try:
                            delete_project(project_id)
                            st.success(f"✅ Projet '{nom_projet}' supprimé!")
                            del st.session_state[f'confirm_del_{project_id}']
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur: {str(e)}")
                    else:
                        st.session_state[f'confirm_del_{project_id}'] = True
                        st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression")


def show_catalog_manager():
    """Interface de gestion du catalogue de produits"""

    st.divider()
    st.subheader("⚙️ Gestion du catalogue de produits")

    catalog = st.session_state.takeoff_catalog

    tab1, tab2, tab3 = st.tabs(["📦 Produits", "➕ Ajouter", "📥 Import/Export"])

    with tab1:
        categories = catalog.get_categories()

        if categories:
            for category in categories:
                with st.expander(f"📁 {category}"):
                    products = catalog.get_products_by_category(category)

                    for product_name, product_data in products.items():
                        col1, col2, col3 = st.columns([3, 2, 1])

                        with col1:
                            st.write(f"**{product_name}**")
                            st.caption(product_data['dimensions'])

                        with col2:
                            st.write(f"{product_data['price']:.2f}$ / {product_data['price_unit']}")

                        with col3:
                            if st.button("🗑️", key=f"del_prod_{category}_{product_name}"):
                                catalog.delete_product(category, product_name)
                                catalog.save_catalog()
                                st.rerun()
        else:
            st.info("Aucun produit dans le catalogue")

    with tab2:
        st.write("Ajouter un nouveau produit")

        with st.form("add_product_form"):
            new_category = st.text_input("Catégorie (nouvelle ou existante)")
            new_product_name = st.text_input("Nom du produit")
            new_dimensions = st.text_input("Dimensions/Description")

            col1, col2 = st.columns(2)
            with col1:
                new_price = st.number_input("Prix unitaire", min_value=0.0, step=0.1)
            with col2:
                new_unit = st.selectbox("Unité", options=['pi²', 'm²', 'ft²', 'pi', 'm', 'ft', 'unité', 'paquet', 'feuille'])

            submit_product = st.form_submit_button("✅ Ajouter le produit")

            if submit_product and new_category and new_product_name:
                success = catalog.add_product(
                    new_category,
                    new_product_name,
                    new_dimensions,
                    new_price,
                    new_unit
                )

                if success:
                    catalog.save_catalog()
                    st.success(f"✅ Produit '{new_product_name}' ajouté!")
                    st.rerun()

    with tab3:
        st.write("**Exporter le catalogue**")

        if st.button("📥 Télécharger le catalogue"):
            catalog_json = catalog.export_catalog_to_string()

            st.download_button(
                label="💾 Télécharger (JSON)",
                data=catalog_json,
                file_name=f"catalogue_takeoff_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

        st.divider()
        st.write("**Importer un catalogue**")

        uploaded_catalog = st.file_uploader(
            "Fichier JSON",
            type=['json'],
            key='catalog_import'
        )

        if uploaded_catalog:
            if st.button("📤 Importer"):
                success = catalog.import_catalog_from_file(uploaded_catalog)
                if success:
                    st.success("✅ Catalogue importé avec succès!")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de l'import")
