"""
Vue publique pour que les clients consultent et signent les soumissions
Accessible via lien avec token unique
"""

import streamlit as st
from soumissions_db import get_soumission_by_token, update_soumission_decision
from datetime import datetime


def show_soumission_client_view(token):
    """
    Affiche la soumission pour le client avec possibilité de signer

    Args:
        token: Token unique de la soumission
    """
    # Note: st.set_page_config() est géré dans app.py avant l'appel de cette fonction

    # Récupérer la soumission
    soum = get_soumission_by_token(token)

    if not soum:
        st.error("❌ Soumission introuvable ou lien invalide")
        st.stop()

    # Statut de la soumission
    statut = soum.get('statut', 'Brouillon')

    # CSS pour la page client - Pleine largeur et responsive avec thème complet
    st.markdown("""
    <style>
        /* === VARIABLES CSS === */
        :root {
            --primary-color: #3B82F6;
            --primary-color-darker: #2563EB;
            --button-color: #1F2937;
            --button-color-light: #374151;
            --background-color: #FAFBFF;
            --secondary-background: #F8FAFF;
            --content-background: #FFFFFF;
            --text-color: #1F2937;
            --text-color-light: #6B7280;
            --text-color-muted: #9CA3AF;
            --border-color: #E5E7EB;
            --border-color-blue: #DBEAFE;
            --project-success: #22C55E;
            --project-danger: #EF4444;
            --primary-gradient: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
            --button-gradient: linear-gradient(90deg, #3B82F6 0%, #1F2937 100%);
            --button-gradient-hover: linear-gradient(90deg, #2563EB 0%, #111827 100%);
        }

        /* Masquer le menu Streamlit */
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        header {visibility: hidden !important;}

        /* FORCER PLEINE LARGEUR - VERSION NUCLÉAIRE */
        /* Cibler absolument TOUS les conteneurs */
        html, body, #root, .main, section, div {
            margin: 0 !important;
        }

        /* Containers principaux */
        .main .block-container,
        .block-container,
        div.block-container,
        .stApp > div,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > section,
        section.main,
        section.main > div,
        .css-1d391kg,
        .css-18e3th9,
        .css-12oz5g7,
        .css-uf99v8,
        .e1fqkh3o3 {
            max-width: 100% !important;
            width: 100% !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }

        .main .block-container {
            padding-top: 1rem !important;
        }

        /* Forcer l'iframe pleine largeur */
        iframe {
            width: 100% !important;
            max-width: 100% !important;
        }

        /* Supprimer tous les paddings latéraux excessifs */
        [data-testid="stAppViewContainer"] {
            padding: 0 !important;
        }

        /* Réinitialiser les marges auto qui centrent le contenu */
        * {
            margin-left: 0 !important;
            margin-right: 0 !important;
        }

        /* Exception pour les éléments internes qui ont besoin de marges */
        .client-header,
        .signature-section,
        .status-badge,
        p, h1, h2, h3, h4, h5, h6 {
            margin-left: auto !important;
            margin-right: auto !important;
        }

        /* En-tête client */
        .client-header {
            background: var(--primary-gradient) !important;
            color: white !important;
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 24px rgba(31, 41, 55, 0.25);
        }

        .client-header h1,
        .client-header p,
        .client-header * {
            color: white !important;
        }

        /* Badges de statut */
        .status-badge {
            display: inline-block;
            padding: 0.5rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            margin-top: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .status-brouillon { background: var(--text-color-muted); color: white; }
        .status-acceptee { background: var(--project-success); color: white; }
        .status-refusee { background: var(--project-danger); color: white; }
        .status-envoyee { background: var(--primary-color); color: white; }

        /* Section signature */
        .signature-section {
            background: var(--secondary-background);
            border: 2px dashed var(--border-color-blue);
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem 0;
        }

        .signature-section h2 {
            color: var(--text-color);
            margin-top: 0;
        }

        .signature-section p {
            color: var(--text-color-light);
        }

        .signature-canvas {
            border: 2px solid var(--primary-color);
            border-radius: 8px;
            background: var(--content-background);
            cursor: crosshair;
        }

        /* Boutons d'action */
        .action-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 2rem;
        }

        /* Boutons Streamlit */
        button[kind="primary"] {
            background: var(--button-gradient) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }

        button[kind="primary"]:hover {
            background: var(--button-gradient-hover) !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        }

        button[kind="secondary"] {
            background: var(--content-background) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }

        button[kind="secondary"]:hover {
            background: var(--secondary-background) !important;
            border-color: var(--primary-color) !important;
        }

        /* Dividers */
        hr {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 2rem 0;
        }

        /* Messages success/error */
        .stSuccess {
            background: #DCFCE7 !important;
            color: var(--text-color) !important;
            border-left: 4px solid var(--project-success) !important;
        }

        .stError {
            background: #FEE2E2 !important;
            color: var(--text-color) !important;
            border-left: 4px solid var(--project-danger) !important;
        }

        .stInfo {
            background: var(--secondary-background) !important;
            color: var(--text-color) !important;
            border-left: 4px solid var(--primary-color) !important;
        }

        /* Inputs de formulaire */
        input[type="text"] {
            border-radius: 8px !important;
            border: 1px solid var(--border-color) !important;
            padding: 0.75rem !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
        }

        input[type="text"]:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        }

        /* Texte général */
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            color: var(--text-color) !important;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            color: var(--text-color) !important;
            font-weight: 700 !important;
        }

        /* Responsive mobile */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }

            .client-header {
                padding: 1rem;
            }

            .client-header h1 {
                font-size: 1.5rem !important;
            }

            .signature-section {
                padding: 1rem;
            }

            .action-buttons {
                flex-direction: column;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # En-tête
    status_class = f"status-{statut.lower()}"
    st.markdown(f"""
    <div class="client-header">
        <h1 style="margin: 0; font-size: 2.5rem; color: white;">📋 Soumission {soum['numero_soumission']}</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9; color: white;">
            {soum['client_nom']}
        </p>
        <div class="{status_class} status-badge">
            {statut.upper()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Si déjà signée (acceptée ou refusée)
    if statut in ['Acceptée', 'Refusée']:
        show_signed_soumission(soum)
    else:
        # Soumission en attente de signature
        show_pending_soumission(soum, token)


def show_pending_soumission(soum, token):
    """Affiche la soumission en attente avec formulaire de signature"""

    # Télécharger la soumission
    st.markdown("### 📄 Consulter la soumission")

    if soum.get('html_content'):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("💡 Téléchargez le fichier HTML ci-dessous, puis ouvrez-le avec votre navigateur pour consulter la soumission complète")
        with col2:
            st.download_button(
                label="⬇️ Télécharger HTML",
                data=soum['html_content'],
                file_name=f"Soumission_{soum.get('numero_soumission', 'Document')}.html",
                mime="text/html",
                use_container_width=True
            )

        st.markdown("---")
    else:
        st.warning("Contenu HTML non disponible")
        # Afficher les infos de base
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Projet:** {soum.get('projet_description', 'N/A')}")
            st.write(f"**Type:** {soum.get('projet_type', 'N/A')}")
        with col2:
            st.write(f"**Montant total:** {soum.get('investissement_total', 0):,.2f} $")
            st.write(f"**Date:** {soum.get('date_creation', 'N/A')}")

    st.markdown("---")

    # Section signature
    st.markdown("""
    <div class="signature-section">
        <h2 style="color: #1e293b; margin-top: 0;">✍️ Signature électronique</h2>
        <p style="color: #64748b;">
            Pour accepter ou refuser cette soumission, veuillez signer ci-dessous et cliquer sur le bouton approprié.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Formulaire de signature simplifié
    with st.form(key="signature_form"):
        st.markdown("### ✍️ Informations de signature")

        nom_signataire = st.text_input(
            "Nom complet du signataire *",
            placeholder="Ex: Jean Tremblay",
            help="Entrez votre nom complet tel qu'il apparaîtra sur la soumission"
        )

        # Afficher la date actuelle (lecture seule)
        from datetime import datetime
        date_signature = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"📅 **Date de signature :** {date_signature}")

        st.markdown("---")

        # Boutons d'action
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            submit_approve = st.form_submit_button(
                "✅ ACCEPTER LA SOUMISSION",
                use_container_width=True,
                type="primary"
            )

        with col2:
            submit_reject = st.form_submit_button(
                "❌ REFUSER LA SOUMISSION",
                use_container_width=True
            )

        with col3:
            st.form_submit_button(
                "🖨️ IMPRIMER",
                use_container_width=True,
                on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            )

        # Traitement de la soumission
        if submit_approve or submit_reject:
            if not nom_signataire:
                st.error("❌ Veuillez entrer votre nom complet")
            else:
                action = 'approve' if submit_approve else 'reject'

                # Enregistrer la décision avec le nom du signataire uniquement
                success = update_soumission_decision(
                    token=token,
                    action=action,
                    signature_data=None,  # Pas de signature dessinée
                    signature_nom=nom_signataire
                )

                if success:
                    st.success(f"✅ Soumission {'acceptée' if action == 'approve' else 'refusée'} avec succès !")
                    st.balloons() if action == 'approve' else st.snow()
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de l'enregistrement de la décision")


def show_signed_soumission(soum):
    """Affiche une soumission déjà signée (acceptée ou refusée)"""

    statut = soum.get('statut')

    # Message de confirmation
    if statut == 'Acceptée':
        st.success(f"""
        ### ✅ Soumission Acceptée

        Cette soumission a été acceptée le **{soum.get('date_decision', 'N/A')}**

        **Signataire:** {soum.get('signature_nom', 'N/A')}
        """)
    else:
        st.error(f"""
        ### ❌ Soumission Refusée

        Cette soumission a été refusée le **{soum.get('date_decision', 'N/A')}**

        **Signataire:** {soum.get('signature_nom', 'N/A')}
        """)

    st.markdown("---")

    # Télécharger la soumission
    st.markdown("### 📄 Consulter la soumission")

    if soum.get('html_content'):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("💡 Téléchargez le fichier HTML ci-dessous, puis ouvrez-le avec votre navigateur pour consulter la soumission complète")
        with col2:
            st.download_button(
                label="⬇️ Télécharger HTML",
                data=soum['html_content'],
                file_name=f"Soumission_{soum.get('numero_soumission', 'Document')}.html",
                mime="text/html",
                use_container_width=True
            )

        st.markdown("---")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Projet:** {soum.get('projet_description', 'N/A')}")
            st.write(f"**Type:** {soum.get('projet_type', 'N/A')}")
        with col2:
            st.write(f"**Montant total:** {soum.get('investissement_total', 0):,.2f} $")
            st.write(f"**Date création:** {soum.get('date_creation', 'N/A')}")

    # Bouton imprimer
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🖨️ IMPRIMER", use_container_width=True):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
