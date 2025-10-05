"""
Interface utilisateur pour la gestion des soumissions sauvegardées
"""

import streamlit as st
from soumissions_db import get_all_soumissions, get_soumission_by_id, update_soumission_statut, delete_soumission, get_soumissions_stats
from datetime import datetime


def show_soumissions_management():
    """Affiche l'interface de gestion des soumissions"""

    # En-tête du module avec style
    st.markdown("""
    <style>
        .module-header {
            background: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 24px rgba(31, 41, 55, 0.25);
        }
        .module-header h2 {
            color: white !important;
            margin: 0;
        }
    </style>
    <div class="module-header">
        <h2>💼 Gestion des Soumissions</h2>
    </div>
    """, unsafe_allow_html=True)

    # Bouton fermer
    if st.button("❌ Fermer", use_container_width=True, key="close_soumissions_management"):
        st.session_state.show_soumissions_management = False
        st.rerun()

    # Statistiques en haut
    stats = get_soumissions_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total soumissions", stats['total'])
    with col2:
        st.metric("Montant total", f"{stats['montant_total']:,.2f} $")
    with col3:
        st.metric("Montant moyen", f"{stats['montant_moyen']:,.2f} $")
    with col4:
        brouillons = stats['par_statut'].get('Brouillon', {}).get('count', 0)
        st.metric("Brouillons", brouillons)

    st.markdown("---")

    # Onglets
    tab1, tab2 = st.tabs(["📋 Liste des soumissions", "📊 Statistiques"])

    with tab1:
        # Filtres
        col1, col2 = st.columns([3, 1])
        with col1:
            filtre_statut = st.selectbox(
                "Filtrer par statut",
                options=["Tous", "Brouillon", "Envoyée", "Acceptée", "Refusée"],
                key="filtre_statut_soumissions"
            )
        with col2:
            limit = st.number_input("Nombre max", min_value=10, max_value=200, value=50, step=10)

        # Récupérer les soumissions
        if filtre_statut == "Tous":
            soumissions = get_all_soumissions(limit=limit)
        else:
            soumissions = get_all_soumissions(limit=limit, statut=filtre_statut)

        if not soumissions:
            st.info("Aucune soumission trouvée.")
        else:
            st.markdown(f"**{len(soumissions)} soumission(s) trouvée(s)**")

            # En-tête du tableau
            st.markdown("""
            <style>
                .soum-table-header {
                    display: grid;
                    grid-template-columns: 1fr 2fr 1.5fr 1.5fr 1fr 1fr 0.8fr 0.8fr;
                    gap: 10px;
                    background: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
                    color: white;
                    padding: 12px;
                    border-radius: 8px 8px 0 0;
                    font-weight: 600;
                    font-size: 0.9rem;
                }
                .soum-table-row {
                    display: grid;
                    grid-template-columns: 1fr 2fr 1.5fr 1.5fr 1fr 1fr 0.8fr 0.8fr;
                    gap: 10px;
                    padding: 12px;
                    border-bottom: 1px solid #E5E7EB;
                    align-items: center;
                    background: white;
                    transition: background 0.2s;
                }
                .soum-table-row:hover {
                    background: #FAFBFF;
                }
            </style>
            <div class="soum-table-header">
                <div>N° Soumission</div>
                <div>👤 Client</div>
                <div>🏗️ Projet</div>
                <div>📐 Type</div>
                <div>📅 Date</div>
                <div>💰 Montant</div>
                <div>👁️ Voir</div>
                <div>🔗 Lien</div>
            </div>
            """, unsafe_allow_html=True)

            # Afficher les soumissions dans le tableau
            for soum in soumissions:
                date_obj = datetime.strptime(soum['date_creation'], '%Y-%m-%d %H:%M:%S')

                # Badge de statut
                statut = soum['statut']
                if statut == 'Brouillon':
                    badge_color = "#94a3b8"
                elif statut == 'Envoyée':
                    badge_color = "#3B82F6"
                elif statut == 'Acceptée':
                    badge_color = "#10b981"
                else:  # Refusée
                    badge_color = "#ef4444"

                # Ligne du tableau
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 2, 1.5, 1.5, 1, 1, 0.8, 0.8])

                with col1:
                    st.markdown(f"**#{soum['numero_soumission']}**")
                    st.markdown(f"""
                    <div style="background: {badge_color}; color: white; padding: 0.2rem 0.4rem;
                                border-radius: 3px; text-align: center; font-size: 0.7rem; font-weight: 600; margin-top: 4px;">
                        {statut}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"**{soum['client_nom']}**")

                with col3:
                    projet_desc = soum.get('projet_description', '')
                    if projet_desc and len(projet_desc) > 30:
                        st.caption(f"{projet_desc[:30]}...")
                    elif projet_desc:
                        st.caption(projet_desc)
                    else:
                        st.caption("_Non spécifié_")

                with col4:
                    projet_type = soum.get('projet_type', 'N/A')
                    superficie = soum.get('projet_superficie', 0)
                    st.markdown(f"{projet_type}")
                    if superficie > 0:
                        st.caption(f"{superficie:,.0f} pi²")

                with col5:
                    st.markdown(date_obj.strftime('%d/%m/%Y'))

                with col6:
                    st.markdown(f"**{soum['investissement_total']:,.0f} $**")

                with col7:
                    if st.button("👁️", key=f"view_{soum['id']}", use_container_width=True, help="Voir les détails"):
                        st.session_state.view_soumission_id = soum['id']
                        st.rerun()

                with col8:
                    # Récupérer le lien public de la soumission
                    soum_complete = get_soumission_by_id(soum['id'])
                    lien_public = soum_complete.get('lien_public') if soum_complete else None

                    if lien_public:
                        # Bouton pour copier le lien
                        if st.button("📋", key=f"copy_{soum['id']}", use_container_width=True, help="Copier le lien client"):
                            # Afficher le lien à copier
                            st.session_state[f'show_link_{soum["id"]}'] = True
                            st.rerun()

                st.divider()

                # Afficher le lien si demandé
                if st.session_state.get(f'show_link_{soum["id"]}', False):
                    soum_complete = get_soumission_by_id(soum['id'])
                    lien = soum_complete.get('lien_public', 'Lien non disponible')
                    st.code(lien, language=None)
                    if st.button("✅ Fermer", key=f"close_link_{soum['id']}"):
                        st.session_state[f'show_link_{soum["id"]}'] = False
                        st.rerun()

    with tab2:
        st.markdown("### 📊 Statistiques détaillées")

        # Répartition par statut
        if stats['par_statut']:
            st.markdown("#### Répartition par statut")
            for statut, data in stats['par_statut'].items():
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.markdown(f"**{statut}**")
                with col2:
                    st.metric("Nombre", data['count'])
                with col3:
                    st.metric("Montant total", f"{data['total']:,.2f} $")

        # Graphique simple
        st.markdown("#### Montants par statut")
        chart_data = {}
        for statut, data in stats['par_statut'].items():
            chart_data[statut] = data['total']

        if chart_data:
            st.bar_chart(chart_data)


def show_soumission_detail(soumission_id):
    """Affiche les détails d'une soumission spécifique"""

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"## 📄 Détails de la soumission #{soumission_id}")
    with col2:
        if st.button("◀️ Retour", use_container_width=True, key="back_from_detail"):
            st.session_state.pop('view_soumission_id', None)
            st.rerun()

    # Charger la soumission
    soum = get_soumission_by_id(soumission_id)

    if not soum:
        st.error("Soumission introuvable")
        return

    # Informations principales
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 👤 Client")
        st.write(f"**Nom:** {soum['client_nom']}")
        st.write(f"**N° Soumission:** {soum['numero_soumission']}")

    with col2:
        st.markdown("### 🏗️ Projet")
        st.write(f"**Type:** {soum['projet_type']}")
        st.write(f"**Superficie:** {soum['projet_superficie']:,.0f} pi²")
        if soum['projet_description']:
            st.write(f"**Description:** {soum['projet_description'][:100]}...")

    with col3:
        st.markdown("### 💰 Montants")
        st.write(f"**Total travaux:** {soum['total_travaux']:,.2f} $")
        st.write(f"**Administration:** {soum['administration']:,.2f} $")
        st.write(f"**Contingences:** {soum['contingences']:,.2f} $")
        st.write(f"**Profit:** {soum['profit']:,.2f} $")
        st.markdown(f"**Total:** <span style='color: #10b981; font-size: 1.2rem; font-weight: bold;'>{soum['investissement_total']:,.2f} $</span>", unsafe_allow_html=True)

    st.markdown("---")

    # Lien public pour le client
    if soum.get('lien_public'):
        st.markdown("### 🔗 Lien Public Client")
        st.info("Partagez ce lien avec votre client pour qu'il puisse consulter et signer la soumission en ligne.")
        st.code(soum['lien_public'], language=None)

        # Afficher si la soumission a été signée
        if soum.get('signature_nom'):
            st.success(f"""
            ✅ **Soumission signée par:** {soum['signature_nom']}
            - **Date de décision:** {soum.get('date_decision', 'N/A')}
            - **Statut:** {soum.get('statut', 'N/A')}
            """)

    st.markdown("---")

    # Gestion du statut
    col1, col2 = st.columns([3, 1])

    with col1:
        nouveau_statut = st.selectbox(
            "Changer le statut",
            options=["Brouillon", "Envoyée", "Acceptée", "Refusée"],
            index=["Brouillon", "Envoyée", "Acceptée", "Refusée"].index(soum['statut']),
            key=f"statut_{soumission_id}"
        )

        notes = st.text_area(
            "Notes",
            value=soum.get('notes', ''),
            key=f"notes_{soumission_id}",
            height=100
        )

    with col2:
        if st.button("💾 Sauvegarder", use_container_width=True):
            update_soumission_statut(soumission_id, nouveau_statut, notes)
            st.success("✅ Statut mis à jour !")
            st.rerun()

        if st.button("🗑️ Supprimer", use_container_width=True):
            if st.session_state.get(f'confirm_delete_soum_{soumission_id}'):
                delete_soumission(soumission_id)
                st.session_state.pop('view_soumission_id', None)
                st.success("✅ Soumission supprimée !")
                st.rerun()
            else:
                st.session_state[f'confirm_delete_soum_{soumission_id}'] = True
                st.warning("⚠️ Cliquez à nouveau pour confirmer")

    st.markdown("---")

    # Afficher le HTML
    st.markdown("### 📄 Aperçu HTML")

    if soum.get('html_content'):
        # Bouton de téléchargement
        st.download_button(
            label="⬇️ Télécharger HTML",
            data=soum['html_content'].encode('utf-8'),
            file_name=f"Soumission_{soum['numero_soumission']}.html",
            mime="text/html",
            use_container_width=True
        )

        # Aperçu dans un iframe (optionnel - peut être lourd)
        with st.expander("👁️ Voir l'aperçu", expanded=False):
            st.components.v1.html(soum['html_content'], height=2000, scrolling=True)
    else:
        st.warning("Aucun contenu HTML disponible")
