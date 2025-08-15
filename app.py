# app.py (Version fusionnée - SANS mot de passe)
import streamlit as st
import os
import io
import html
import markdown
from datetime import datetime
from dotenv import load_dotenv

# Importer les classes logiques et le gestionnaire de conversation
try:
    from expert_logic import ExpertAdvisor, ExpertProfileManager
    from conversation_manager import ConversationManager
    from security_utils import (
        log_security_event, LoginAttemptTracker, 
        validate_environment_variables, sanitize_input, check_rate_limiting
    )
except ImportError as e:
    st.error(f"Erreur d'importation des modules locaux: {e}")
    st.error("Assurez-vous que tous les fichiers requis existent dans le même dossier.")
    st.stop()

# Modules supprimés : project_manager, inventory_manager, database_integration, knowledge_base_ui

# --- Configuration de la Page Principale ---
st.set_page_config(
    page_title="EXPERTS IA",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Fonction pour charger le CSS local ---
def local_css(file_name):
    """Charge les styles CSS depuis un fichier local."""
    try:
        css_path = os.path.join(os.path.dirname(__file__), file_name)
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Fichier CSS '{file_name}' non trouvé dans {os.path.dirname(__file__)}.")
    except Exception as e:
        st.error(f"Erreur lors du chargement du CSS '{file_name}': {e}")

# --- Helper Function pour lire le CSS pour l'intégration HTML ---
@st.cache_data
def load_css_content(file_name):
    """Charge le contenu brut d'un fichier CSS."""
    try:
        css_path = os.path.join(os.path.dirname(__file__), file_name)
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.warning(f"Fichier CSS '{file_name}' non trouvé pour l'intégration HTML.")
        return "/* CSS non trouvé */"
    except Exception as e:
        st.error(f"Erreur lors de la lecture du CSS '{file_name}' pour l'intégration : {e}")
        return f"/* Erreur lecture CSS: {e} */"

# --- Fonction helper pour convertir image en base64 ---
def get_image_base64(image_path):
    """Convertit une image en base64 pour l'incorporation HTML."""
    import base64
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"Erreur lors de la lecture de l'image: {e}")
        return ""

# --- Fonction pour détecter si on est sur mobile ---
def is_mobile_device():
    """Estimation si l'appareil est mobile basée sur la largeur de viewport."""
    # Si non défini ou première visite, définir par défaut comme non-mobile
    if 'is_mobile' not in st.session_state:
        st.session_state.is_mobile = False

    # JavaScript pour détecter la largeur d'écran et mettre à jour via le localStorage
    st.markdown("""
    <script>
    // Vérifier si l'appareil a une petite largeur d'écran
    const checkIfMobile = function() {
        const isMobile = window.innerWidth < 768;
        localStorage.setItem('streamlit_is_mobile', isMobile);
        return isMobile;
    };
    
    // Exécuter au chargement et à chaque redimensionnement
    checkIfMobile();
    window.addEventListener('resize', checkIfMobile);
    
    // Essayer de communiquer avec Streamlit
    window.addEventListener('message', function(event) {
        if (event.data.type === 'streamlit:render') {
            setTimeout(function() {
                const buttons = document.querySelectorAll('button[data-baseweb="button"]');
                if (buttons.length > 0) {
                    // Ajouter un attribut data-mobile pour utilisation future
                    buttons.forEach(function(button) {
                        button.setAttribute('data-is-mobile', checkIfMobile());
                    });
                }
            }, 500);
        }
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Retourner la valeur actuelle
    return st.session_state.is_mobile

# --- Fonction pour adapter la mise en page en fonction de la détection mobile ---
def adapt_layout_for_mobile(is_mobile):
    """Adapte la mise en page en fonction de la détection mobile."""
    if is_mobile:
        # Style spécifique pour mobile
        st.markdown("""
        <style>
        /* Styles spécifiques pour mobile */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Augmenter la taille des boutons pour faciliter l'interaction tactile */
        div.stButton > button {
            min-height: 44px !important;
            font-size: 16px !important;
            width: 100% !important;
        }
        
        /* Réduire les marges et paddings */
        div.stChatMessage {
            padding: 12px !important;
            margin-bottom: 12px !important;
        }
        
        /* Simplifier certains conteneurs */
        .main-header {
            padding: 15px !important;
            margin-bottom: 15px !important;
        }
        
        /* Adaptation de la sidebar */
        [data-testid="stSidebar"][aria-expanded="true"] {
            width: 85vw !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Style desktop normal
        pass

# --- Fonction pour afficher le résultat d'analyse avec un style amélioré ---
def display_analysis_result(analysis_response, analysis_details):
    """Affiche le résultat d'analyse avec un style amélioré."""
    st.markdown("""
    <style>
    .analysis-container {
        animation: fadeIn 0.6s ease-out;
        background: linear-gradient(to right, #f0f7ff, #e6f3ff);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 25px;
        border-left: 5px solid #3B82F6;
    }
    .analysis-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        color: #1e40af;
    }
    .analysis-header h2 {
        margin: 0;
        font-size: 22px;
        font-weight: 600;
    }
    .analysis-header h2::before {
        content: "🔍 ";
        margin-right: 8px;
    }
    .analysis-section {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        border-left: 3px solid #60A5FA;
    }
    .analysis-section h3 {
        color: #3B82F6;
        font-size: 18px;
        margin-top: 0;
        margin-bottom: 10px;
    }
    </style>
    <div class="analysis-container">
        <div class="analysis-header">
            <h2>Analyse des documents</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Convertir le texte d'analyse en HTML avec sections
    content = analysis_response
    sections = content.split("**")
    
    for i in range(1, len(sections), 2):
        if i+1 < len(sections):
            section_title = sections[i].strip(":** ")
            section_content = sections[i+1]
            
            st.markdown(f"""
            <div class="analysis-section">
                <h3>{section_title}</h3>
                <div>{section_content}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- Fonction de Génération HTML ---
def generate_html_report(messages, profile_name, conversation_id=None, client_name=""):
    """Génère un rapport HTML autonome à partir de l'historique."""
    custom_css = load_css_content("style.css")
    now = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    conv_id_display = f" (ID: {conversation_id})" if conversation_id else ""
    client_display = f"<p><strong>Client :</strong> {html.escape(client_name)}</p>" if client_name else ""
    messages_html = ""
    md_converter = markdown.Markdown(extensions=['tables', 'fenced_code'])

    # Ajouter les styles supplémentaires pour l'export
    custom_css += """
    body {
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
        color: #333;
        background-color: #f9fafb;
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    .report-header {
        background: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(31, 41, 55, 0.25);
        text-align: center;
        color: white;
        border: 1px solid #374151;
    }
    .report-header h1 {
        margin: 0;
        color: white;
        font-size: 2.2rem;
        font-weight: 600;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    .report-info {
        background: linear-gradient(135deg, #DBEAFE 0%, #FFFFFF 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #3B82F6;
    }
    .conversation-history {
        padding-top: 1.5rem;
    }
    .stChatMessage {
        margin-bottom: 1.5rem;
        padding: 1rem 1.2rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        animation: fadeIn 0.5s ease-out;
        position: relative;
        max-width: 85%;
    }
    .stChatMessage.user-bubble {
        background: linear-gradient(to right, #f0f7ff, #e6f3ff);
        border-left: 4px solid #60A5FA;
        margin-left: auto;
        margin-right: 0;
    }
    .stChatMessage.user-bubble::after {
        content: "";
        position: absolute;
        top: 15px;
        right: -10px;
        border-width: 10px 0 10px 10px;
        border-style: solid;
        border-color: transparent transparent transparent #e6f3ff;
    }
    .stChatMessage.assistant-bubble {
        background: linear-gradient(to right, #f7f9fc, #ffffff);
        border-left: 4px solid #3B82F6;
        margin-left: 0;
        margin-right: auto;
    }
    .stChatMessage.assistant-bubble::after {
        content: "";
        position: absolute;
        top: 15px;
        left: -10px;
        border-width: 10px 10px 10px 0;
        border-style: solid;
        border-color: transparent #f7f9fc transparent transparent;
    }
    .stChatMessage.search-bubble {
        background: linear-gradient(to right, #f0fdf4, #e6f7ec);
        border-left: 4px solid #22c55e;
        margin-right: 4rem;
        color: #14532D;
    }
    .stChatMessage.search-bubble .msg-content p,
    .stChatMessage.search-bubble .msg-content ul,
    .stChatMessage.search-bubble .msg-content ol {
        color: #14532D;
    }
    .stChatMessage.other-bubble {
        background: linear-gradient(to right, #DBEAFE 0%, #FFFFFF 100%);
        border-left: 4px solid #60A5FA;
    }
    .msg-content strong {
        font-weight: 600;
    }
    .msg-content table {
        font-size: 0.9em;
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        border-radius: 0.375rem;
        overflow: hidden;
    }
    .msg-content th, .msg-content td {
        border: 1px solid #E5E7EB;
        padding: 0.6em 0.9em;
        text-align: left;
    }
    .msg-content th {
        background-color: #F3F4F6;
        font-weight: 500;
        color: #374151;
    }
    .msg-content tr:nth-child(even) {
        background-color: #F9FAFB;
    }
    .msg-content tr:hover {
        background-color: #DBEAFE;
    }
    .msg-content pre {
        background-color: #1F2937;
        color: #F9FAFB;
        padding: 1em;
        border-radius: 0.5rem;
        overflow-x: auto;
        border: 1px solid #4B5563;
        margin: 1em 0;
        font-size: 0.85rem;
        line-height: 1.5;
    }
    .msg-content pre code {
        background-color: transparent;
        color: inherit;
        padding: 0;
        margin: 0;
        font-size: inherit;
        border-radius: 0;
        font-family: "monospace", monospace;
        display: block;
        white-space: pre;
        line-height: 1.5;
    }
    .msg-content code {
        background-color: #E5E7EB;
        padding: 0.2em 0.4em;
        margin: 0 0.1em;
        font-size: 85%;
        border-radius: 0.375rem;
        font-family: "monospace", monospace;
        color: #374151;
    }
    section[data-testid=stSidebar],
    div[data-testid=stChatInput],
    .stButton,
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"] {
        display: none !important;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    /* Responsive design */
    @media (max-width: 768px) {
        body {
            padding: 1rem;
        }
        .report-header {
            padding: 1.5rem;
        }
        .report-header h1 {
            font-size: 1.8rem;
        }
        .stChatMessage {
            max-width: 95%;
            padding: 0.8rem 1rem;
        }
        .stChatMessage.user-bubble,
        .stChatMessage.assistant-bubble {
            margin-left: 0;
            margin-right: 0;
        }
        .stChatMessage.user-bubble::after,
        .stChatMessage.assistant-bubble::after {
            display: none;
        }
    }
    """

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "*Message vide*")

        if role == "system": 
            continue

        try:
            md_converter.reset()
            content_str = str(content) if not isinstance(content, str) else content
            content_html = md_converter.convert(content_str)
        except Exception as e:
            print(f"Erreur conversion Markdown: {e}")
            content_html = f"<p>{html.escape(str(content)).replace(chr(10), '<br/>')}</p>"

        # Déterminer le style de bulle et le label
        if role == "user":
            bubble_class = "user-bubble"
            role_label = "Utilisateur"
        elif role == "assistant":
            bubble_class = "assistant-bubble"
            role_label = f"Expert ({html.escape(profile_name)})"
        elif role == "search_result":
            bubble_class = "search-bubble"
            role_label = "Résultat Recherche Web"
        else:
            bubble_class = "other-bubble"
            role_label = html.escape(role.capitalize())

        messages_html += f'''
        <div class="stChatMessage {bubble_class}">
            <strong>{role_label} :</strong>
            <div class="msg-content">{content_html}</div>
        </div>
        '''

    html_output = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport EXPERTS IA - {html.escape(profile_name)}{conv_id_display}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>{custom_css}</style>
</head>
<body>
    <div class="report-header">
        <h1>🏗️ Rapport EXPERTS IA</h1>
    </div>
    <div class="report-info">
        <p><strong>Expert :</strong> {html.escape(profile_name)}</p>
        {client_display}
        <p><strong>Date :</strong> {now}</p>
        <p><strong>ID Conversation :</strong> {html.escape(str(conversation_id)) if conversation_id else 'N/A'}</p>
    </div>
    <div class="conversation-history">
        {messages_html}
    </div>
</body>
</html>"""
    
    return html_output
   
# --- [DEBUT DE LA SECTION FUSIONNÉE] Fonction pour exporter un message individuel (de la Version 02) ---
def generate_single_message_html(message_content, message_role, profile_name, message_index=0, timestamp=None):
    """Génère HTML pour un message individuel avec style professionnel amélioré."""
    
    if not timestamp:
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    
    base_css = load_css_content("style.css")
    
    if message_role == "user":
        role_display = "Utilisateur"
        bubble_class = "user-bubble"
        avatar_icon = "👤"
        header_color = "#60A5FA"
        gradient_colors = "#f0f7ff, #e6f3ff"
    elif message_role == "search_result":
        role_display = "Résultat Recherche Web"
        bubble_class = "search-bubble"
        avatar_icon = "🔎"
        header_color = "#22c55e"
        gradient_colors = "#f0fdf4, #e6f7ec"
    else:
        role_display = f"Expert ({profile_name})"
        bubble_class = "assistant-bubble"
        avatar_icon = "🏗️"
        header_color = "#3B82F6"
        gradient_colors = "#f7f9fc, #ffffff"
    
    # Conversion markdown avec gestion d'erreurs robuste
    try:
        md_converter = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite'])
        md_converter.reset()
        content_html = md_converter.convert(str(message_content))
    except Exception as e:
        print(f"Erreur conversion Markdown: {e}")
        # Fallback sécurisé
        escaped_content = html.escape(str(message_content))
        content_html = f"<p>{escaped_content.replace(chr(10), '<br/>')}</p>"
    
    # CSS spécialisé avec tous les styles du rapport + styles spécifiques au message individuel
    specialized_css = f"""
    {base_css}
    
    body {{
        max-width: 1000px;
        margin: 20px auto;
        padding: 20px;
        background-color: #f9fafb;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
        color: #333;
    }}
    
    .single-message-container {{
        background: white;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        padding: 0;
        overflow: hidden;
        border: 1px solid #e5e7eb;
        animation: fadeIn 0.8s ease-out;
    }}
    
    .message-header {{
        background: linear-gradient(135deg, {header_color}15 0%, {header_color}08 100%);
        padding: 25px 30px;
        border-bottom: 1px solid #e5e7eb;
        border-left: 5px solid {header_color};
        position: relative;
        overflow: hidden;
    }}
    
    .message-header::before {{
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%);
        animation: header-shine 3s infinite;
        z-index: 1;
    }}
    
    .message-header h1 {{
        margin: 0;
        color: {header_color};
        font-size: 1.9rem;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 700;
        position: relative;
        z-index: 2;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }}
    
    .message-meta {{
        margin-top: 15px;
        font-size: 0.9rem;
        color: #6b7280;
        display: flex;
        gap: 25px;
        flex-wrap: wrap;
        position: relative;
        z-index: 2;
    }}
    
    .meta-item {{
        display: flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.7);
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 500;
    }}
    
    .message-content {{ 
        padding: 30px;
        line-height: 1.7;
        background: linear-gradient(to right, {gradient_colors});
        border-left: 4px solid {header_color};
        position: relative;
    }}
    
    /* Styles pour le contenu - identiques au rapport */
    .message-content h1, .message-content h2, .message-content h3 {{
        color: #1f2937;
        font-weight: 700;
        margin-top: 1.5em;
        margin-bottom: 0.8em;
    }}
    
    .message-content h1 {{
        font-size: 1.8rem;
        border-bottom: 3px solid {header_color};
        padding-bottom: 8px;
    }}
    
    .message-content h2 {{
        font-size: 1.4rem;
        color: {header_color};
    }}
    
    .message-content h3 {{
        font-size: 1.2rem;
        color: #374151;
    }}
    
    .message-content table {{
        width: 100%;
        border-collapse: collapse;
        margin: 1.5em 0;
        font-size: 0.9rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-radius: 8px;
        overflow: hidden;
        background: white;
    }}
    
    .message-content th, .message-content td {{
        border: 1px solid #e5e7eb;
        padding: 12px 15px;
        text-align: left;
    }}
    
    .message-content th {{
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        font-weight: 600;
        color: #374151;
        border-bottom: 2px solid #d1d5db;
        position: relative;
    }}
    
    .message-content tr:nth-child(even) {{
        background-color: #f9fafb;
    }}
    
    .message-content tr:hover {{
        background: linear-gradient(to right, #dbeafe, #f0f7ff);
        transform: translateX(2px);
        transition: all 0.3s ease;
    }}
    
    .message-content strong {{
        font-weight: 700;
        color: #1f2937;
    }}
    
    .message-content code {{
        background: linear-gradient(135deg, #e5e7eb 0%, #f3f4f6 100%);
        padding: 3px 6px;
        margin: 0 2px;
        font-size: 0.9em;
        border-radius: 4px;
        font-family: 'Monaco', 'Menlo', monospace;
        color: #374151;
        border: 1px solid #d1d5db;
    }}
    
    .message-content pre {{
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        color: #f9fafb;
        padding: 20px;
        border-radius: 8px;
        overflow-x: auto;
        border: 1px solid #4b5563;
        margin: 1.5em 0;
        font-size: 0.85rem;
        line-height: 1.6;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }}
    
    .message-content pre code {{
        background: transparent;
        color: inherit;
        padding: 0;
        margin: 0;
        font-size: inherit;
        border: none;
        border-radius: 0;
    }}
    
    .message-content hr {{
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, {header_color} 50%, transparent 100%);
        margin: 2em 0;
    }}
    
    .message-content ol, .message-content ul {{
        padding-left: 1.5em;
        margin: 1em 0;
    }}
    
    .message-content li {{
        margin-bottom: 0.5em;
        line-height: 1.6;
    }}
    
    .export-footer {{
        text-align: center;
        padding: 25px;
        border-top: 1px solid #e5e7eb;
        background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
        font-size: 0.85rem;
        color: #6b7280;
    }}
    
    .export-footer .logo {{
        color: {header_color};
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    @keyframes header-shine {{
        0%, 50% {{ left: -100%; }}
        100% {{ left: 100%; }}
    }}
    
    /* Responsive design amélioré */
    @media (max-width: 768px) {{
        body {{ padding: 15px; }}
        .single-message-container {{ border-radius: 12px; }}
        .message-header {{ padding: 20px; }}
        .message-header h1 {{ font-size: 1.6rem; }}
        .message-content {{ padding: 20px; }}
        .message-meta {{ gap: 15px; }}
        .meta-item {{ font-size: 0.8rem; }}
        .message-content table {{ font-size: 0.8rem; }}
        .message-content th, .message-content td {{ padding: 8px 10px; }}
    }}
    
    @media (max-width: 480px) {{
        body {{ padding: 10px; }}
        .message-header {{ padding: 15px; }}
        .message-header h1 {{ font-size: 1.4rem; }}
        .message-content {{ padding: 15px; }}
        .message-meta {{ flex-direction: column; gap: 8px; }}
    }}
    """
    
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message EXPERTS IA - {role_display}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>{specialized_css}</style>
</head>
<body>
    <div class="single-message-container">
        <div class="message-header">
            <h1>{avatar_icon} {html.escape(role_display)}</h1>
            <div class="message-meta">
                <div class="meta-item">
                    <span>📅</span>
                    <span>Exporté le {timestamp}</span>
                </div>
                <div class="meta-item">
                    <span>#️⃣</span>
                    <span>Message #{message_index + 1}</span>
                </div>
                <div class="meta-item">
                    <span>📏</span>
                    <span>{len(str(message_content)):,} caractères</span>
                </div>
                <div class="meta-item">
                    <span>🏷️</span>
                    <span>Type: {message_role.title()}</span>
                </div>
            </div>
        </div>
        <div class="message-content">
            {content_html}
        </div>
        <div class="export-footer">
            <div class="logo">🏗️ EXPERTS IA</div>
            <p><strong>Assistant IA Spécialisé en Construction au Québec</strong></p>
            <p>Développé par Sylvain Leduc - <a href="mailto:info@constructoai.ca" style="color: {header_color};">info@constructoai.ca</a></p>
            <p><small>Document généré automatiquement • Tous droits réservés</small></p>
        </div>
    </div>
</body>
</html>"""
    
    return html_content

# --- [FIN DE LA SECTION FUSIONNÉE] ---

# --- Helper Functions (Application Logic) ---
def start_new_consultation():
    """Réinitialise l'état pour une nouvelle conversation."""
    st.session_state.messages = []
    st.session_state.current_conversation_id = None
    st.session_state.processed_messages = set()
    
    # Réinitialiser aussi l'état des autres modules
    # Variables de session des modules supprimés nettoyées
    
    profile_name = "par défaut"
    if 'expert_advisor' in st.session_state:
        profile = st.session_state.expert_advisor.get_current_profile()
        profile_name = profile.get('name', 'par défaut') if profile else "par défaut"
    
    # Message d'accueil mis à jour
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Bonjour! Je suis votre expert {profile_name}. Comment puis-je vous aider aujourd'hui?\n\n"
                   f"**Commandes rapides :**\n"
                   f"• `/search` + question → Recherche web"
    })
    
    # Nettoyer les variables d'état
    for key in ['html_download_data', 'single_message_download', 'show_copy_content', 'files_to_analyze']:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

def load_selected_conversation(conv_id):
    """Charge une conversation depuis la base de données."""
    if st.session_state.conversation_manager:
        messages = st.session_state.conversation_manager.load_conversation(conv_id)
        if messages is not None:
            st.session_state.messages = messages
            st.session_state.current_conversation_id = conv_id
            st.session_state.processed_messages = set()
            if 'html_download_data' in st.session_state: del st.session_state.html_download_data
            if 'single_message_download' in st.session_state: del st.session_state.single_message_download
            if 'show_copy_content' in st.session_state: del st.session_state.show_copy_content
            if "files_to_analyze" in st.session_state: del st.session_state.files_to_analyze
            st.success(f"Consultation {conv_id} chargée.")
            st.rerun()
        else:
            st.error(f"Erreur lors du chargement de la conversation {conv_id}.")
    else:
        st.error("Gestionnaire de conversations indisponible.")

def delete_selected_conversation(conv_id):
    """Supprime une conversation de la base de données."""
    if st.session_state.conversation_manager:
        print(f"Tentative suppression conv {conv_id}")
        success = st.session_state.conversation_manager.delete_conversation(conv_id)
        if success:
            st.success(f"Consultation {conv_id} supprimée.")
            if st.session_state.current_conversation_id == conv_id:
                # Variables de session des modules supprimés nettoyées
                start_new_consultation() # Rerun inclus
            else:
                if 'html_download_data' in st.session_state: del st.session_state.html_download_data
                if 'single_message_download' in st.session_state: del st.session_state.single_message_download
                if 'show_copy_content' in st.session_state: del st.session_state.show_copy_content
                st.rerun() # Juste pour rafraîchir la liste
        else:
            st.error(f"Impossible de supprimer conv {conv_id}.")
    else:
        st.error("Gestionnaire de conversations indisponible.")

def save_current_conversation():
    """Sauvegarde la conversation actuelle (messages) dans la DB."""
    should_save = True
    if st.session_state.conversation_manager and st.session_state.messages:
        is_initial_greeting_only = (
            len(st.session_state.messages) == 1 and
            st.session_state.messages[0].get("role") == "assistant" and
            st.session_state.messages[0].get("content", "").startswith("Bonjour!") and
            st.session_state.current_conversation_id is None
        )
        if is_initial_greeting_only: should_save = False

        if should_save:
            try:
                new_id = st.session_state.conversation_manager.save_conversation(
                    st.session_state.current_conversation_id,
                    st.session_state.messages
                )
                if new_id is not None and st.session_state.current_conversation_id is None:
                    st.session_state.current_conversation_id = new_id
            except Exception as e:
                st.warning(f"Erreur sauvegarde auto: {e}")
                st.exception(e)

# --- Fonction Export Sidebar Section ---
def create_export_sidebar_section():
    """Section d'export complète pour la sidebar."""
    
    st.markdown('<div class="sidebar-subheader">📥 EXPORT</div>', unsafe_allow_html=True)
    
    # Export conversation complète (conserver l'existant)
    client_name_export = st.text_input("Nom client (optionnel)", key="client_name_export", placeholder="Pour rapport HTML")
    
    st.markdown("""
    <style>
    div.stButton > button:has(span:contains("Rapport HTML")) {
        background: linear-gradient(90deg, #93c5fd 0%, #60a5fa 100%) !important;
        color: white !important; font-weight: 600 !important; border: none !important;
    }
    div.stButton > button:has(span:contains("Rapport HTML"))::before { content: "📄 " !important; }
    div.stButton > button:has(span:contains("Rapport HTML")):hover {
        background: linear-gradient(90deg, #60a5fa 0%, #3b82f6 100%) !important;
        transform: translateY(-2px) !important; box-shadow: 0 4px 8px rgba(59, 130, 246, 0.2) !important;
    }
    div.stButton > button:has(span:contains("Télécharger HTML")) {
        background: linear-gradient(90deg, #bbf7d0 0%, #86efac 100%) !important;
        color: #166534 !important; font-weight: 600 !important; border: none !important;
    }
    div.stButton > button:has(span:contains("Télécharger HTML"))::before { content: "⬇️ " !important; }
    div.stButton > button:has(span:contains("Télécharger HTML")):hover {
        background: linear-gradient(90deg, #86efac 0%, #4ade80 100%) !important;
        transform: translateY(-2px) !important; box-shadow: 0 4px 8px rgba(22, 101, 52, 0.2) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("Rapport HTML", key="gen_html_btn", use_container_width=True, help="Générer rapport HTML"):
        st.session_state.html_download_data = None
        can_generate = True
        if not st.session_state.messages or (len(st.session_state.messages) == 1 and st.session_state.messages[0].get("role") == "assistant" and st.session_state.messages[0].get("content", "").startswith("Bonjour!")):
            can_generate = False
        if not can_generate:
            st.warning("Conversation vide ou initiale.")
        else:
            with st.spinner("Génération HTML..."):
                try:
                    profile_name = "Expert"
                    current_profile = st.session_state.expert_advisor.get_current_profile() if 'expert_advisor' in st.session_state else None
                    if current_profile: profile_name = current_profile.get('name', 'Expert')
                    conv_id = st.session_state.current_conversation_id
                    html_string = generate_html_report(st.session_state.messages, profile_name, conv_id, client_name_export)
                    if html_string:
                        id_part = f"Conv{conv_id}" if conv_id else datetime.now().strftime('%Y%m%d_%H%M')
                        filename = f"Rapport_EXPERTS_IA_{id_part}.html"
                        st.session_state.html_download_data = {"data": html_string, "filename": filename}
                        st.success("Rapport prêt.")
                    else:
                        st.error("Échec génération HTML.")
                except Exception as e:
                    st.error(f"Erreur génération HTML: {e}")
                    st.exception(e)
        st.rerun()
        
    if st.session_state.get('html_download_data'):
        download_info = st.session_state.html_download_data
        st.download_button(
            label="⬇️ Télécharger HTML",
            data=download_info["data"].encode("utf-8"),
            file_name=download_info["filename"],
            mime="text/html",
            key="dl_html",
            use_container_width=True,
            on_click=lambda: st.session_state.update(html_download_data=None)
        )
    
    # === NOUVELLE SECTION : EXPORT MESSAGES INDIVIDUELS ===
    st.markdown("---")
    st.markdown('<div class="sidebar-subheader">📤 MESSAGES INDIVIDUELS</div>', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.caption("Aucun message à exporter.")
        return
    
    # Filtrer les messages exportables
    exportable_messages = []
    for i, msg in enumerate(st.session_state.messages):
        if msg.get("role") in ["assistant", "search_result"] and msg.get("content", "").strip():
            role_display = "🏗️ Expert" if msg["role"] == "assistant" else "🔎 Recherche"
            content_preview = str(msg["content"])[:40] + "..." if len(str(msg["content"])) > 40 else str(msg["content"])
            exportable_messages.append({
                "index": i,
                "display": f"{role_display}: {content_preview}",
                "role": msg["role"],
                "content": msg["content"]
            })
    
    if not exportable_messages:
        st.caption("Aucun message expert à exporter.")
        return
    
    # Sélecteur de message
    selected_msg = st.selectbox(
        "Message à exporter:",
        options=exportable_messages,
        format_func=lambda x: x["display"],
        key="export_message_selector",
        label_visibility="collapsed"
    )
    
    if selected_msg:
        # Aperçu condensé
        with st.expander("👀 Aperçu", expanded=False):
            content_preview = str(selected_msg['content'])
            if len(content_preview) > 150:
                st.markdown(content_preview[:150] + "...")
                st.caption(f"Total: {len(content_preview)} caractères")
            else:
                st.markdown(content_preview)
        
        # Boutons d'export
        if st.button("📄 Exporter en HTML", key="export_single_html", use_container_width=True):
            try:
                profile = st.session_state.expert_advisor.get_current_profile()
                profile_name = profile.get('name', 'Expert') if profile else 'Expert'
                
                html_content = generate_single_message_html(
                    selected_msg['content'], 
                    selected_msg['role'], 
                    profile_name, 
                    selected_msg['index']
                )
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"Message_EXPERTS_IA_{selected_msg['role']}_{selected_msg['index']}_{timestamp}.html"
                
                # Stocker pour téléchargement
                st.session_state.single_message_download = {
                    "data": html_content,
                    "filename": filename
                }
                
                st.success("✅ Fichier prêt pour téléchargement")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erreur lors de l'export: {e}")
        
        # Bouton de téléchargement si prêt
        if st.session_state.get('single_message_download'):
            download_data = st.session_state.single_message_download
            st.download_button(
                label="⬇️ Télécharger HTML",
                data=download_data["data"].encode('utf-8'),
                file_name=download_data["filename"],
                mime="text/html",
                key="download_single_message",
                use_container_width=True,
                on_click=lambda: st.session_state.pop('single_message_download', None)
            )
        
        # Option copie texte
        if st.button("📋 Afficher pour Copie", key="show_for_copy", use_container_width=True):
            st.session_state.show_copy_content = selected_msg['content']
            st.rerun()
        
        # Affichage pour copie si demandé
        if st.session_state.get('show_copy_content'):
            st.text_area(
                "Contenu à copier:",
                value=st.session_state.show_copy_content,
                height=150,
                key="copy_content_area"
            )
            if st.button("❌ Fermer", key="close_copy"):
                st.session_state.pop('show_copy_content', None)
                st.rerun()

# --- Charger Police Google Font & CSS pour l'App ---
st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        /* Styles inline spécifiques à l'UI Streamlit (peuvent être dans style.css) */
        .sidebar-subheader {
            margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 0.875rem;
            font-weight: 500; color: var(--text-color-light);
            text-transform: uppercase; letter-spacing: 0.05em;
        }
        /* Styles pour l'historique dans la sidebar */
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="secondary"] {
            text-align: left; justify-content: flex-start !important;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
            font-size: 0.9rem; padding: 0.4rem 0.6rem;
            border: 1px solid transparent; background-color: transparent;
            color: var(--text-color); transition: background-color 0.2s ease, border-color 0.2s ease;
        }
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="secondary"]:hover {
            background-color: var(--border-color-light); border-color: var(--border-color);
        }
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="secondary"] {
            background: none; border: none; color: var(--text-color-light); cursor: pointer;
            padding: 0.4rem 0.3rem; font-size: 0.9rem; line-height: 1;
        }
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="secondary"]:hover {
            color: #EF4444; background-color: rgba(239, 68, 68, 0.1);
        }

        /* Styles pour la base de connaissances */
        .kb-card {
            background: linear-gradient(135deg, #f0f7ff 0%, #e6f3ff 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
            border-left: 4px solid #3B82F6;
            transition: all 0.3s ease;
        }

        .kb-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }

        .kb-profile-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border-left: 3px solid #10B981;
        }

        .kb-document-card {
            background: #f8fafc;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            border-left: 3px solid #6366F1;
        }

        .kb-tag {
            display: inline-block;
            background: #DBEAFE;
            color: #1E40AF;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            margin-right: 5px;
            margin-bottom: 3px;
        }

        .kb-stats-container {
            background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid #bbf7d0;
        }

        /* Styles des modules supprimés nettoyés */
        
        /* Styles des modules d'inventaire supprimés */
    </style>
""", unsafe_allow_html=True)
local_css("style.css") # Recharger pour s'assurer que les styles de l'app sont appliqués

# --- Détection de l'appareil mobile ---
is_mobile = is_mobile_device()
adapt_layout_for_mobile(is_mobile)

# --- Load API Keys ---
load_dotenv() # Pour le dev local si .env existe

# Obtenir la clé API depuis les variables d'environnement ou secrets
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    try:
        ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        pass

# --- SYSTÈME D'AUTHENTIFICATION SÉCURISÉ ---
@st.cache_data(ttl=300)  # Cache pendant 5 minutes
def get_login_tracker():
    """Obtient le tracker de connexions (cache pour performance)."""
    return LoginAttemptTracker()

def check_authentication():
    """Vérifie l'authentification de l'utilisateur avec sécurité renforcée."""
    # Valider les variables d'environnement critiques
    missing_vars = validate_environment_variables()
    if missing_vars:
        st.error("❌ Configuration manquante!")
        st.error(f"Variables requises: {', '.join(missing_vars)}")
        st.info("💡 Configurez les variables d'environnement ou secrets Streamlit")
        log_security_event("MISSING_CONFIG", f"Variables: {missing_vars}", "CRITICAL")
        st.stop()
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        login_tracker = get_login_tracker()
        
        # Vérifier si l'utilisateur est bloqué
        if login_tracker.is_locked_out():
            remaining_time = login_tracker.get_lockout_time_remaining()
            if remaining_time:
                minutes_remaining = int(remaining_time.total_seconds() // 60)
                st.error(f"🔒 **Accès temporairement bloqué**")
                st.error(f"Trop de tentatives de connexion échouées.")
                st.error(f"Réessayez dans {minutes_remaining} minute(s).")
                st.info("💡 Contactez l'administrateur si vous avez oublié le mot de passe")
                st.stop()
        # Styles pour la page de connexion
        st.markdown("""
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            margin: 2rem 0;
            padding: 3rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        .login-header {
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        .login-header p {
            font-size: 1.1rem;
            opacity: 0.9;
            margin: 0;
        }
        .login-form {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
        }
        .stTextInput > div > div > input {
            font-size: 1.1rem;
            padding: 0.75rem;
            border-radius: 8px;
            border: 2px solid #e1e5e9;
            transition: all 0.3s ease;
        }
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        div.stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            font-size: 1.1rem;
            padding: 0.75rem 2rem;
            border-radius: 8px;
            border: none;
            width: 100%;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .security-notice {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 1rem;
            margin-top: 1rem;
            color: white;
            text-align: center;
            font-size: 0.9rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="login-container">
            <div class="login-header">
                <h1>🏗️ EXPERTS IA</h1>
                <p>Plateforme Sécurisée d'Experts en Construction</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Interface de connexion dans un conteneur centré
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.markdown('<div class="login-form">', unsafe_allow_html=True)
                
                st.markdown("### 🔐 Authentification Requise")
                st.markdown("Veuillez saisir le mot de passe d'accès pour utiliser la plateforme.")
                
                password = st.text_input(
                    "Mot de passe", 
                    type="password",
                    placeholder="Entrez votre mot de passe...",
                    help="Contactez l'administrateur si vous n'avez pas le mot de passe"
                )
                
                # Afficher les tentatives restantes
                remaining = login_tracker.get_remaining_attempts()
                if remaining < 5:
                    if remaining > 0:
                        st.warning(f"⚠️ {remaining} tentative(s) restante(s) avant blocage")
                    else:
                        st.error("❌ Plus de tentatives autorisées")
                
                if st.button("🚀 Se Connecter", key="login_button"):
                    # Vérifier la limite de taux
                    if not check_rate_limiting():
                        st.error("❌ Trop de requêtes. Attendez un moment.")
                        st.stop()
                    
                    # Sanitiser l'entrée
                    password = sanitize_input(password)
                    
                    # Obtenir le mot de passe depuis les variables d'environnement
                    app_password = os.environ.get("APP_PASSWORD")
                    if not app_password:
                        try:
                            app_password = st.secrets.get("APP_PASSWORD")
                        except Exception:
                            pass
                    
                    if not app_password:
                        st.error("❌ Configuration manquante: APP_PASSWORD non défini")
                        st.info("💡 L'administrateur doit configurer la variable APP_PASSWORD")
                        log_security_event("MISSING_APP_PASSWORD", "Configuration critique manquante", "CRITICAL")
                        st.stop()
                    
                    if password == app_password:
                        st.session_state.authenticated = True
                        login_tracker.record_successful_login()
                        st.success("✅ Authentification réussie ! Redirection...")
                        log_security_event("SUCCESSFUL_AUTH", "Utilisateur connecté", "INFO")
                        time.sleep(1)
                        st.rerun()
                    else:
                        login_tracker.record_failed_attempt()
                        remaining_after = login_tracker.get_remaining_attempts()
                        
                        if remaining_after > 0:
                            st.error("❌ Mot de passe incorrect")
                            st.warning(f"🔒 {remaining_after} tentative(s) restante(s)")
                        else:
                            st.error("❌ Compte temporairement bloqué")
                            st.error("Trop de tentatives échouées")
                            
                        log_security_event("FAILED_AUTH", f"Tentative échouée, {remaining_after} restantes", "WARNING")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Notice de sécurité
        st.markdown("""
        <div class="security-notice">
            🛡️ <strong>Sécurité:</strong> Cette application utilise une authentification sécurisée.<br>
            Toutes les connexions sont surveillées et les tentatives d'accès non autorisé sont bloquées.
        </div>
        """, unsafe_allow_html=True)
        
        st.stop()

# Appliquer l'authentification
check_authentication()

# --- Initialize Logic Classes & Conversation Manager ---
if 'profile_manager' not in st.session_state:
    try:
        profile_dir_path = "profiles"
        if not os.path.exists(profile_dir_path):
            os.makedirs(profile_dir_path, exist_ok=True); print(f"Dossier '{profile_dir_path}' créé.")
            default_profile_path = os.path.join(profile_dir_path, "default_expert.txt")
            if not os.path.exists(default_profile_path):
                with open(default_profile_path, "w", encoding="utf-8") as f: f.write("Expert par Défaut\nJe suis un expert IA généraliste."); print("Profil par défaut créé.")
        st.session_state.profile_manager = ExpertProfileManager(profile_dir=profile_dir_path)
        print("ProfileManager initialisé.")
    except Exception as e: st.error(f"Erreur critique: Init ProfileManager: {e}"); st.stop()

if 'expert_advisor' not in st.session_state:
    if not ANTHROPIC_API_KEY: st.error("Erreur critique: ANTHROPIC_API_KEY non configurée."); st.stop()
    try:
        st.session_state.expert_advisor = ExpertAdvisor(api_key=ANTHROPIC_API_KEY)
        st.session_state.expert_advisor.profile_manager = st.session_state.profile_manager
        print("ExpertAdvisor initialisé.")
        available_profiles = st.session_state.profile_manager.get_profile_names()
        if available_profiles:
            initial_profile_name = available_profiles[0]
            st.session_state.selected_profile_name = initial_profile_name
            st.session_state.expert_advisor.set_current_profile_by_name(initial_profile_name)
            print(f"Profil initial chargé: {initial_profile_name}")
        else:
            st.warning("Aucun profil expert trouvé. Utilisation profil par défaut.")
            default_profile = st.session_state.expert_advisor.get_current_profile()
            st.session_state.selected_profile_name = default_profile.get("name", "Expert (Défaut)")
    except Exception as e: st.error(f"Erreur critique: Init ExpertAdvisor: {e}"); st.exception(e); st.stop()

if 'conversation_manager' not in st.session_state:
    try:
        db_file_path = "conversations.db"
        st.session_state.conversation_manager = ConversationManager(db_path=db_file_path)
        print(f"ConversationManager initialisé avec DB: {os.path.abspath(db_file_path)}")
    except Exception as e: st.error(f"Erreur: Init ConversationManager: {e}"); st.exception(e); st.session_state.conversation_manager = None; st.warning("Historique désactivé.")




# Initialisation variables état session
if "messages" not in st.session_state: st.session_state.messages = []
if "current_conversation_id" not in st.session_state: st.session_state.current_conversation_id = None
if "processed_messages" not in st.session_state: st.session_state.processed_messages = set()
if 'single_message_download' not in st.session_state: st.session_state.single_message_download = None
if 'show_copy_content' not in st.session_state: st.session_state.show_copy_content = None

# --- Sidebar UI (App Principale) ---
with st.sidebar:
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            # Style professionnel sans fond coloré et logo plus grand
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; align-items: center; 
                            width: 100%; margin-bottom: 2rem; padding: 1rem 0;">
                    <div style="transition: all 0.3s ease-in-out; cursor: pointer;" 
                            onmouseover="this.style.transform='scale(1.05)'; this.style.filter='drop-shadow(0 8px 16px rgba(0, 0, 0, 0.1))';"
                            onmouseout="this.style.transform='scale(1)'; this.style.filter='drop-shadow(0 2px 4px rgba(0, 0, 0, 0.05))';">
                        <img src="data:image/png;base64,{get_image_base64(logo_path)}" 
                            style="width: 210px; height: auto; filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.05));">
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("Logo 'assets/logo.png' non trouvé.")
    except Exception as e:
        st.error(f"Erreur logo: {e}")
        
    # Améliorez le bouton "Nouvelle Consultation"
    st.markdown("""
    <style>
    div.stButton > button:has(span:contains("Nouvelle Consultation")) {
        background: linear-gradient(90deg, #60A5FA 0%, #3B82F6 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 10px 15px !important;
        position: relative !important;
    }
    div.stButton > button:has(span:contains("Nouvelle Consultation"))::before {
        content: "✨ " !important;
    }
    div.stButton > button:has(span:contains("Nouvelle Consultation")):hover {
        background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(59, 130, 246, 0.2) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Bouton de déconnexion ---
    st.markdown("""
    <style>
    div.stButton > button:has(span:contains("Se Déconnecter")) {
        background: linear-gradient(90deg, #EF4444 0%, #DC2626 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
        font-size: 0.9rem !important;
        border-radius: 6px !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:has(span:contains("Se Déconnecter")):hover {
        background: linear-gradient(90deg, #DC2626 0%, #B91C1C 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(239, 68, 68, 0.3) !important;
    }
    div.stButton > button:has(span:contains("Se Déconnecter"))::before {
        content: "🚪 " !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Se Déconnecter", key="logout_button"):
            # Effacer toutes les données de session sensibles
            if 'authenticated' in st.session_state:
                del st.session_state.authenticated
            if 'messages' in st.session_state:
                del st.session_state.messages
            if 'current_conversation_id' in st.session_state:
                del st.session_state.current_conversation_id
            # Effacer toute la session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("🔒 Déconnexion réussie")
            time.sleep(1)
            st.rerun()
    
    with col1:
        pass  # Espace vide pour aligner le bouton à droite
    
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)

    if st.button("Nouvelle Consultation", key="new_consult_button_top", use_container_width=True):
        save_current_conversation()
        start_new_consultation()
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)

    # --- Profil Expert ---
    st.markdown('<div class="sidebar-subheader">👤 PROFIL EXPERT</div>', unsafe_allow_html=True)
    if 'expert_advisor' in st.session_state and st.session_state.expert_advisor.profile_manager:
        profile_names = st.session_state.expert_advisor.profile_manager.get_profile_names()
        if profile_names:
            try:
                selected_profile_name_ref = st.session_state.get("selected_profile_name", profile_names[0])
                current_index = profile_names.index(selected_profile_name_ref) if selected_profile_name_ref in profile_names else 0
            except ValueError:
                current_index = 0
            selected_profile = st.selectbox("Profil:", profile_names, index=current_index, key="profile_select", label_visibility="collapsed")
            if selected_profile != st.session_state.get("selected_profile_name"):
                print(f"Changement profil: '{st.session_state.get('selected_profile_name')}' -> '{selected_profile}'")
                save_current_conversation()
                
                # NOUVEAU : Tracker l'utilisation du profil précédent
                if st.session_state.get("selected_profile_name") and 'db_integration' in st.session_state:
                    track_expert_usage(st.session_state.get("selected_profile_name"), success=True)
                
                with st.spinner(f"Changement vers {selected_profile}..."):
                    success = st.session_state.expert_advisor.set_current_profile_by_name(selected_profile)
                    if success:
                        st.session_state.selected_profile_name = selected_profile
                        
                        # NOUVEAU : Logger le changement de profil
                        # Le tracking des changements de profil n'est plus disponible
                        
                        st.success(f"Profil changé. Nouvelle consultation.")
                        start_new_consultation() # Rerun inclus
                    else:
                        st.error(f"Impossible de charger profil '{selected_profile}'.")
        else:
            st.warning("Aucun profil expert trouvé.")
    else:
        st.error("Module Expert non initialisé.")

    # --- Analyse Fichiers ---
    st.markdown('<div class="sidebar-subheader">📄 ANALYSE FICHIERS</div>', unsafe_allow_html=True)
    uploaded_files_sidebar = [] # Initialisation par défaut
    if 'expert_advisor' in st.session_state:
        supported_types = st.session_state.expert_advisor.get_supported_filetypes_flat()
        uploaded_files_sidebar = st.file_uploader(
            "Téléverser fichiers:",
            type=supported_types if supported_types else None,
            accept_multiple_files=True,
            key="file_uploader_sidebar",
            label_visibility="collapsed"
        )

        # Déterminer si le bouton doit être désactivé
        is_disabled = not bool(uploaded_files_sidebar)

        # Style pour le bouton d'analyse
        st.markdown("""
        <style>
        div.stButton > button:has(span:contains("Analyser")) {
            background: linear-gradient(90deg, #c5e1a5 0%, #aed581 100%) !important;
            color: #33691e !important;
            border: none !important;
            animation: pulse 2s infinite;
        }
        div.stButton > button:has(span:contains("Analyser"))::before {
            content: "🔍 " !important;
        }
        div.stButton > button:has(span:contains("Analyser")):hover {
            background: linear-gradient(90deg, #aed581 0%, #9ccc65 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(51, 105, 30, 0.2) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Afficher le bouton, en utilisant l'état désactivé
        if st.button("🔍 Analyser Fichiers", key="analyze_button", use_container_width=True, disabled=is_disabled):
            # Cette partie ne s'exécute que si le bouton est cliqué ET n'était PAS désactivé
            if not is_disabled:
                num_files = len(uploaded_files_sidebar)
                file_names_str = ', '.join([f.name for f in uploaded_files_sidebar])
                user_analysis_prompt = f"J'ai téléversé {num_files} fichier(s) ({file_names_str}) pour analyse. Peux-tu les examiner ?"
                action_id = f"analyze_{datetime.now().isoformat()}"
                # Stocker les fichiers à analyser DANS l'état de session pour les récupérer après le rerun
                st.session_state.files_to_analyze = uploaded_files_sidebar
                st.session_state.messages.append({"role": "user", "content": user_analysis_prompt, "id": action_id})
                save_current_conversation()
                st.rerun()

         


    # --- Aide Recherche Web (Nouvelle section) ---
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subheader">🔎 RECHERCHE WEB</div>', unsafe_allow_html=True)
    with st.expander("Comment utiliser la recherche web"):
        st.markdown("""
        Pour effectuer une recherche web via Claude:

        1. Tapez `/search` suivi de votre question ou requête
        2. Exemple: `/search normes électriques Québec`
        3. Pour rechercher des informations sur un site spécifique:
            `/search règlement construction site:rbq.gouv.qc.ca`
        4. Attendez quelques secondes pour les résultats

        **Remarque:** Pour obtenir les meilleurs résultats, formulez des questions précises et utilisez des mots-clés pertinents.
        """)
                              
    # --- Manuel d'Utilisation (Nouvelle section) ---
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subheader">📖 MANUEL & AIDE</div>', unsafe_allow_html=True)
    
    # Style pour le bouton du manuel
    st.markdown("""
    <style>
    .manual-button {
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.4) 0%, #3B82F6 20%, #2563EB 80%, rgba(0, 0, 0, 0.2) 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 12px 16px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3), inset 0 -1px 0 rgba(0, 0, 0, 0.1);
        width: 100%;
        text-align: center;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
        text-decoration: none !important;
        font-size: 14px;
        cursor: pointer;
    }
    
    .manual-button::before {
        content: "";
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.4) 50%, transparent 100%);
        transition: left 0.6s ease;
        z-index: 1;
    }
    
    .manual-button:hover::before {
        left: 100%;
    }
    
    .manual-button:hover {
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.5) 0%, #60A5FA 20%, #2563EB 80%, rgba(0, 0, 0, 0.3) 100%);
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(59, 130, 246, 0.35), inset 0 2px 0 rgba(255, 255, 255, 0.4), inset 0 -2px 0 rgba(0, 0, 0, 0.15), 0 0 20px rgba(59, 130, 246, 0.2);
        text-decoration: none !important;
        color: white !important;
    }
    
    .manual-button:visited {
        color: white !important;
        text-decoration: none !important;
    }
    
    .manual-button:link {
        color: white !important;
        text-decoration: none !important;
    }
    
    .manual-button-content {
        position: relative;
        z-index: 2;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Lien direct vers le manuel
    manual_url = "https://constructoai.github.io/MANUEL_UTILISATION_EXPERTS_IA/"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid #0891b2;
        font-size: 0.9rem;
        color: #164e63;
        text-align: center;
    ">
        📖 <strong>Manuel d'Utilisation :</strong><br>
        <a href="{manual_url}" target="_blank" style="color: #0891b2; font-weight: bold; text-decoration: none;">
        Lien
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Informations complémentaires
    with st.expander("💡 Aide Rapide"):
        st.markdown("""
        **🚀 Pour commencer :**
        1. Sélectionnez un expert dans la liste
        2. Posez votre question de construction
        3. Utilisez `/search` pour rechercher sur le web
        4. Explorez les modules Projet et Base de Connaissances
        
        **📞 Support :**
        - Email : support@constructoai.ca
        - Manuel complet : Cliquez le bouton ci-dessus
        """)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 8px;
        padding: 12px;
        margin-top: 8px;
        border-left: 3px solid #0891b2;
        font-size: 0.85rem;
        color: #164e63;
    ">
        <strong>💡 Astuce :</strong> Le manuel s'ouvre dans un nouvel onglet et contient des guides détaillés avec captures d'écran.
    </div>
    """, unsafe_allow_html=True)

    # --- Historique ---
    if st.session_state.get('conversation_manager'):
        st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-subheader">🕒 HISTORIQUE</div>', unsafe_allow_html=True)
        try:
            conversations = st.session_state.conversation_manager.list_conversations(limit=100)
            if not conversations: st.caption("Aucune consultation sauvegardée.")
            else:
                # Style pour les boutons d'historique
                st.markdown("""
                <style>
                div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="secondary"] {
                    text-align: left;
                    justify-content: flex-start !important;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    font-size: 0.9rem;
                    padding: 0.4rem 0.6rem;
                    border: 1px solid transparent;
                    background-color: transparent;
                    color: var(--text-color);
                    transition: all 0.3s;
                    border-radius: 6px;
                }
                div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="secondary"]:hover {
                    background-color: #f0f7ff;
                    border-color: #dbeafe;
                    transform: translateX(3px);
                }
                div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="secondary"] {
                    background: none;
                    border: none;
                    color: var(--text-color-light);
                    cursor: pointer;
                    padding: 0.4rem 0.3rem;
                    font-size: 0.9rem;
                    line-height: 1;
                    transition: all 0.2s;
                    border-radius: 6px;
                }
                div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="secondary"]:hover {
                    color: #EF4444;
                    background-color: rgba(239, 68, 68, 0.1);
                    transform: scale(1.1);
                }
                </style>
                """, unsafe_allow_html=True)
                
                with st.container(height=300):
                    for conv in conversations:
                        col1, col2 = st.columns([0.85, 0.15])
                        with col1:
                            if st.button(conv['name'], key=f"load_conv_{conv['id']}", use_container_width=True, type="secondary", help=f"Charger '{conv['name']}' (màj: {conv['last_updated_at']})"):
                                save_current_conversation(); load_selected_conversation(conv['id'])
                        with col2:
                            if st.button("🗑️", key=f"delete_conv_{conv['id']}", help=f"Supprimer '{conv['name']}'", use_container_width=True, type="secondary"):
                                delete_selected_conversation(conv['id'])
        except Exception as e: st.error(f"Erreur historique: {e}"); st.exception(e)
    else: st.caption("Module historique inactif.")

    # --- Export ---
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
    create_export_sidebar_section()

    # NOUVEAU : Analytics et Statistiques
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subheader">📊 ANALYTICS</div>', unsafe_allow_html=True)

    if 'db_integration' in st.session_state and st.session_state.db_integration:
        
        # Bouton pour afficher les statistiques
        if st.button("📈 Voir Statistiques", use_container_width=True):
            analytics = get_performance_metrics()
            
            if analytics:
                with st.expander("📊 Statistiques d'Utilisation", expanded=True):
                    db_stats = analytics.get("database_stats", {})
                    
                    # Métriques principales
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Conversations", db_stats.get("conversations_count", 0))
                        st.metric("Projets", db_stats.get("projects_count", 0))
                    with col2:
                        st.metric("Messages", db_stats.get("messages_count", 0))
                        st.metric("Documents", db_stats.get("documents_count", 0))
                    
                    # Taille de la base de données
                    db_size = db_stats.get("database_size_mb", 0)
                    st.caption(f"💾 Taille DB: {db_size:.1f} MB")
                    
                    # Experts les plus utilisés
                    st.markdown("#### 🏆 Experts Populaires")
                    top_experts = analytics.get("top_experts", [])
                    for i, expert in enumerate(top_experts[:5], 1):
                        usage = expert.get('usage_count', 0)
                        success_rate = expert.get('success_rate', 0) * 100
                        st.caption(f"{i}. **{expert['name']}** - {usage} utilisations ({success_rate:.0f}% succès)")
        
        # Maintenance de la base de données
        if st.button("🔧 Optimiser Base de Données", use_container_width=True):
            with st.spinner("Optimisation en cours..."):
                try:
                    st.session_state.db_integration.cleanup_and_optimize()
                    st.success("✅ Base de données optimisée!")
                    
                    # Le logging d'optimisation n'est plus disponible
                except Exception as e:
                    st.error(f"Erreur lors de l'optimisation: {e}")
        
        # Affichage de l'activité récente (optionnel)
        with st.expander("🕒 Activité Récente"):
            analytics = get_performance_metrics()
            recent_activity = analytics.get("recent_activity", [])
            
            if recent_activity:
                for activity in recent_activity[:5]:
                    action_time = activity['created_at'][:16].replace('T', ' ')
                    st.caption(f"⏰ {action_time} - {activity['description']}")
            else:
                st.caption("Aucune activité récente")

    else:
        st.caption("Analytics non disponibles")


# --- Main Chat Area (App Principale) ---




main_container = st.container()
with main_container:
    # Titre dynamique avec style amélioré et navigation
    if 'expert_advisor' in st.session_state:
        current_profile = st.session_state.expert_advisor.get_current_profile()
        profile_name = "Assistant EXPERTS IA"
        profile_name = current_profile.get('name', profile_name) if current_profile else profile_name
        
        # Détecter si c'est un profil personnalisé
        is_custom_profile = current_profile and current_profile.get('id', '').startswith('custom_')
        profile_indicator = "🧠 Profil Personnalisé" if is_custom_profile else "👤 Profil Expert"
        
        st.markdown(f"""
        <div class="main-header-premium">
            <div class="header-glow"></div>
            <div class="header-content">
                <div class="header-icon-container">
                    <div class="header-icon">🏗️</div>
                    <div class="icon-ring"></div>
                </div>
                <div class="header-text">
                    <h1 class="header-title">Assistant: {profile_name}</h1>
                    <p class="header-subtitle">{profile_indicator} • Votre expert en construction au Québec</p>
                    <div class="header-status">
                        <span class="status-dot"></span>
                        <span class="status-text">En ligne • Prêt à vous aider</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if current_profile and current_profile.get('id') == 'default_expert': 
            st.info("*Profil expert par défaut actif - Expert en construction au Québec*")
    else: 
        st.markdown("""
        <div class="main-header">
            <h1>🏗️ Assistant EXPERTS IA</h1>
            <p>Erreur: Module expert non initialisé</p>
        </div>
        """, unsafe_allow_html=True)
        st.error("Erreur: Module expert non initialisé.")

    # Affichage du chat
    if not st.session_state.messages and 'expert_advisor' in st.session_state:
        profile = st.session_state.expert_advisor.get_current_profile()
        prof_name = profile.get('name', 'par défaut') if profile else "par défaut"
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Bonjour! Je suis votre expert {prof_name}. Comment puis-je vous aider aujourd'hui?\n\n"
                       f"💡 **Fonctionnalités disponibles**:\n"
                       f"• **Consultation d'expert** : Posez-moi vos questions sur la construction\n"
                       f"• **Analyse de documents** : Uploadez vos plans, devis, ou documents techniques\n"
                       f"• **Recherche web** : Accès aux dernières informations et réglementations\n\n"
                       f"**Commandes rapides :**\n"
                       f"• `/search` + question → Recherche web\n"
                       f"• Uploadez des fichiers pour analyse directe"
        })

    # Style ultra-professionnel et moderne pour les bulles de chat - HARMONISÉ AVEC EXPORT HTML
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Animations harmonisées avec export HTML */
    @keyframes messageSlideIn {
        from { 
            opacity: 0; 
            transform: translateY(20px) scale(0.95);
        }
        to { 
            opacity: 1; 
            transform: translateY(0) scale(1);
        }
    }
    
    @keyframes newMessagePulse {
        0%, 100% { 
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4);
        }
        50% { 
            box-shadow: 0 0 0 15px rgba(59, 130, 246, 0);
        }
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    /* Arrière-plan premium avec texture subtile */
    .main {
        background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
        background-attachment: fixed;
        position: relative;
        min-height: 100vh;
    }
    
    .main::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(147, 197, 253, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(96, 165, 250, 0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Container principal avec glassmorphism subtil */
    .main .block-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1rem;
        position: relative;
        z-index: 1;
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.03),
            0 0 0 1px rgba(255, 255, 255, 0.5) inset;
    }
    
    /* Style global pour toutes les bulles - Premium comme l'export */
    div[data-testid="stChatMessage"] {
        margin-bottom: 1.8rem !important;
        padding: 0 !important;
        border-radius: 16px !important;
        animation: messageSlideIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        container-type: inline-size !important;
    }
    
    div[data-testid="stChatMessage"]:hover {
        transform: translateY(-3px) scale(1.01);
    }
    
    /* Bulles utilisateur - EXACTEMENT comme export HTML */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-user"]) {
        background: linear-gradient(to right, #f0f7ff, #e6f3ff) !important;
        border-left: 4px solid #60A5FA !important;
        border-right: none !important;
        border-top: none !important;
        border-bottom: none !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        max-width: 85% !important;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05) !important;
        position: relative !important;
        overflow: visible !important;
    }
    
    /* Flèche indicatrice utilisateur - comme HTML */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-user"])::after {
        content: "";
        position: absolute;
        top: 15px;
        right: -10px;
        border-width: 10px 0 10px 10px;
        border-style: solid;
        border-color: transparent transparent transparent #e6f3ff;
    }
    
    /* Bulles assistant - EXACTEMENT comme export HTML */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"]) {
        background: linear-gradient(to right, #f7f9fc, #ffffff) !important;
        border-left: 4px solid #3B82F6 !important;
        border-right: none !important;
        border-top: none !important;
        border-bottom: none !important;
        margin-left: 0 !important;
        margin-right: auto !important;
        max-width: 85% !important;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05) !important;
        position: relative !important;
        overflow: visible !important;
    }
    
    /* Flèche indicatrice assistant - comme HTML */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"])::after {
        content: "";
        position: absolute;
        top: 15px;
        left: -10px;
        border-width: 10px 10px 10px 0;
        border-style: solid;
        border-color: transparent #f7f9fc transparent transparent;
    }
    
    /* Bulles recherche - EXACTEMENT comme export HTML */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-search_result"]) {
        background: linear-gradient(to right, #f0fdf4, #e6f7ec) !important;
        border-left: 4px solid #22c55e !important;
        border-right: none !important;
        border-top: none !important;
        border-bottom: none !important;
        margin-left: 0 !important;
        margin-right: 4rem !important;
        max-width: 85% !important;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05) !important;
        color: #14532D !important;
    }
    
    /* Couleur du texte pour recherche */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-search_result"]) p,
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-search_result"]) ul,
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-search_result"]) ol {
        color: #14532D !important;
    }
    
    /* Style du contenu interne des messages */
    div[data-testid="stChatMessage"] > div {
        padding: 1.25rem 1.5rem !important;
        display: flex !important;
        align-items: flex-start !important;
        gap: 1rem !important;
    }
    
    /* Amélioration du contenu formaté - Style premium comme export HTML */
    
    /* Code inline - Style élégant */
    div[data-testid="stChatMessage"] code:not(pre code) {
        background: linear-gradient(135deg, #e5e7eb 0%, #f3f4f6 100%) !important;
        padding: 3px 6px !important;
        margin: 0 2px !important;
        font-size: 0.9em !important;
        border-radius: 4px !important;
        font-family: 'Monaco', 'Menlo', 'Consolas', monospace !important;
        color: #374151 !important;
        border: 1px solid #d1d5db !important;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Code blocks - Style sombre premium */
    div[data-testid="stChatMessage"] pre {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%) !important;
        color: #f9fafb !important;
        padding: 20px !important;
        border-radius: 8px !important;
        overflow-x: auto !important;
        border: 1px solid #4b5563 !important;
        margin: 1.5em 0 !important;
        font-size: 0.85rem !important;
        line-height: 1.6 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    
    div[data-testid="stChatMessage"] pre code {
        background: transparent !important;
        color: inherit !important;
        padding: 0 !important;
        margin: 0 !important;
        font-size: inherit !important;
        border: none !important;
        border-radius: 0 !important;
        font-family: 'Monaco', 'Menlo', monospace !important;
        display: block !important;
        white-space: pre !important;
        line-height: 1.5 !important;
    }
    
    /* Wrapper avec scrollbar horizontale pour les tableaux */
    div[data-testid="stChatMessage"] {
        overflow-x: auto !important;
    }
    
    /* Container avec scrollbar horizontale pour les tableaux */
    div[data-testid="stChatMessage"] table {
        width: 100% !important;
        min-width: 600px !important;
        border-collapse: collapse !important;
        margin: 1.5em 0 !important;
        font-size: 0.9rem !important;
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
    }
    
    /* En-têtes de tableau élargis - Style dégradé subtil - ALIGNEMENT GAUCHE */
    div[data-testid="stChatMessage"] th {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
        font-weight: 600 !important;
        color: #374151 !important;
        text-align: left !important;
        padding: 15px 20px !important;
        border-bottom: 2px solid #d1d5db !important;
        position: relative !important;
        text-transform: uppercase !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.05em !important;
        min-width: 120px !important;
    }
    
    /* Cellules de tableau élargies - Style moderne - ALIGNEMENT GAUCHE */
    div[data-testid="stChatMessage"] td {
        text-align: left !important;
        padding: 15px 20px !important;
        border-bottom: 1px solid #e5e7eb !important;
        vertical-align: middle !important;
        color: #1e40af !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        min-width: 120px !important;
    }
    
    /* Lignes alternées avec effet subtil */
    div[data-testid="stChatMessage"] tr:nth-child(even) td {
        background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%) !important;
    }
    
    /* Effet hover sur les lignes */
    div[data-testid="stChatMessage"] tr:hover td {
        background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%) !important;
        transform: translateX(2px) !important;
        box-shadow: -2px 0 8px rgba(59, 130, 246, 0.1) !important;
    }
    
    
    /* Alignement à gauche pour TOUS les éléments de tableaux */
    div[data-testid="stChatMessage"] table tr > *:first-child,
    div[data-testid="stChatMessage"] table tbody tr > *:first-child,
    div[data-testid="stChatMessage"] table thead tr > *:first-child {
        text-align: left !important;
        color: #1e40af !important;
        font-weight: 500 !important;
    }
    
    /* Alignement à gauche pour les en-têtes premiers */
    div[data-testid="stChatMessage"] table tr > th:first-child,
    div[data-testid="stChatMessage"] table tbody tr > th:first-child,
    div[data-testid="stChatMessage"] table thead tr > th:first-child {
        text-align: left !important;
        color: #262730 !important;
        font-weight: 600 !important;
    }
    
    /* Règle ultra-spécifique pour ALIGNEMENT GAUCHE */
    div[data-testid="stChatMessage"] table tr td:nth-child(1) {
        text-align: left !important;
        color: #1e40af !important;
    }
    
    div[data-testid="stChatMessage"] table tr th:nth-child(1) {
        text-align: left !important;
        color: #262730 !important;
    }
    
    div[data-testid="stChatMessage"] tr:nth-child(even) td {
        background: rgba(59, 130, 246, 0.05) !important;
    }
    
    /* Largeurs élargies pour les colonnes de tableaux - MOINS COMPRESSÉES */
    div[data-testid="stChatMessage"] table td:first-child {
        text-align: left !important;
        max-width: none !important;
        white-space: normal !important;
        width: 50% !important;
        min-width: 200px !important;
        color: #1e40af !important;
        font-weight: 500 !important;
        padding: 15px 20px !important;
    }
    
    div[data-testid="stChatMessage"] table td:last-child {
        text-align: left !important;
        font-weight: 500 !important;
        color: #1e40af !important;
        white-space: nowrap !important;
        width: 25% !important;
        min-width: 120px !important;
        padding: 15px 20px !important;
    }
    
    /* Alignement à gauche pour les colonnes de montants - PLUS LARGES */
    div[data-testid="stChatMessage"] table td:nth-last-child(2) {
        text-align: left !important;
        font-weight: 600 !important;
        color: #1e40af !important;
        width: 25% !important;
        min-width: 120px !important;
        padding: 15px 20px !important;
    }
    
    div[data-testid="stChatMessage"] table td:nth-child(2) {
        text-align: left !important;
        width: 25% !important;
        min-width: 120px !important;
        padding: 15px 20px !important;
    }
    
    div[data-testid="stChatMessage"] table td:nth-child(3) {
        text-align: left !important;
        width: 25% !important;
        min-width: 120px !important;
        padding: 15px 20px !important;
    }
    
    /* Contenu en colonnes pour budgets et estimations */
    div[data-testid="stChatMessage"] .budget-table,
    div[data-testid="stChatMessage"] .estimation-table {
        display: grid !important;
        grid-template-columns: 2fr 1fr 1fr !important;
        gap: 0.5rem !important;
        align-items: center !important;
        padding: 0.5rem 0 !important;
        border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Formatage spécial pour les montants - EXACTEMENT comme export HTML */
    div[data-testid="stChatMessage"] .montant {
        font-weight: bold !important;
        color: #1e40af !important;
        text-align: left !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Amélioration du contenu préformaté */
    div[data-testid="stChatMessage"] .content-area {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        line-height: 1.6 !important;
        font-size: 1rem !important;
    }
    
    div[data-testid="stChatMessage"] .content-area strong {
        color: #1e40af !important;
        font-weight: 600 !important;
    }
    
    /* Typographie premium pour le contenu structuré */
    
    /* Titres - Style moderne avec accent coloré */
    div[data-testid="stChatMessage"] h1 {
        font-family: 'Poppins', 'Inter', sans-serif !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1f2937 !important;
        margin: 1.5em 0 0.8em 0 !important;
        padding-bottom: 8px !important;
        border-bottom: 3px solid #3B82F6 !important;
        position: relative !important;
    }
    
    div[data-testid="stChatMessage"] h2 {
        font-family: 'Poppins', 'Inter', sans-serif !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        color: #3B82F6 !important;
        margin: 1.3em 0 0.7em 0 !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    
    div[data-testid="stChatMessage"] h2::before {
        content: "▸" !important;
        color: #60A5FA !important;
        font-size: 1.2rem !important;
    }
    
    div[data-testid="stChatMessage"] h3 {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
        margin: 1.2em 0 0.6em 0 !important;
        padding-left: 12px !important;
        border-left: 3px solid #60A5FA !important;
    }
    
    /* Paragraphes - Espacement et lisibilité optimale */
    div[data-testid="stChatMessage"] p {
        margin: 0.8em 0 !important;
        line-height: 1.7 !important;
        color: #1f2937 !important;
    }
    
    /* Listes - Style moderne avec puces personnalisées */
    div[data-testid="stChatMessage"] ul,
    div[data-testid="stChatMessage"] ol {
        margin: 1em 0 !important;
        padding-left: 1.5rem !important;
    }
    
    div[data-testid="stChatMessage"] li {
        margin: 0.4em 0 !important;
        line-height: 1.6 !important;
        position: relative !important;
    }
    
    /* Puces personnalisées pour les listes */
    div[data-testid="stChatMessage"] ul li::marker {
        color: #3B82F6 !important;
    }
    
    div[data-testid="stChatMessage"] ol li::marker {
        color: #3B82F6 !important;
        font-weight: 600 !important;
    }
    
    /* Strong/Bold - Accent coloré */
    div[data-testid="stChatMessage"] strong,
    div[data-testid="stChatMessage"] b {
        font-weight: 700 !important;
        color: #1e40af !important;
        letter-spacing: -0.01em !important;
    }
    
    /* Emphasis/Italic - Style subtil */
    div[data-testid="stChatMessage"] em,
    div[data-testid="stChatMessage"] i {
        font-style: italic !important;
        color: #4b5563 !important;
    }
    
    /* Liens - Style moderne avec transition */
    div[data-testid="stChatMessage"] a {
        color: #3B82F6 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        border-bottom: 1px solid transparent !important;
        transition: all 0.2s ease !important;
        position: relative !important;
    }
    
    div[data-testid="stChatMessage"] a:hover {
        color: #2563EB !important;
        border-bottom-color: #2563EB !important;
    }
    
    div[data-testid="stChatMessage"] a::after {
        content: "↗" !important;
        font-size: 0.75em !important;
        margin-left: 2px !important;
        opacity: 0.7 !important;
    }
    
    /* Blockquotes - Style citation élégant */
    div[data-testid="stChatMessage"] blockquote {
        margin: 1em 0 !important;
        padding: 1em 1.5em !important;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%) !important;
        border-left: 4px solid #3B82F6 !important;
        border-radius: 0 8px 8px 0 !important;
        font-style: italic !important;
        position: relative !important;
    }
    
    div[data-testid="stChatMessage"] blockquote::before {
        content: "❝" !important;
        position: absolute !important;
        top: -10px !important;
        left: 10px !important;
        font-size: 3em !important;
        color: #3B82F6 !important;
        opacity: 0.2 !important;
    }
    
    /* Lignes horizontales - Style moderne */
    div[data-testid="stChatMessage"] hr {
        border: none !important;
        height: 2px !important;
        background: linear-gradient(90deg, transparent 0%, #3B82F6 50%, transparent 100%) !important;
        margin: 2em 0 !important;
        position: relative !important;
    }
    
    div[data-testid="stChatMessage"] hr::after {
        content: "✦" !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        background: white !important;
        color: #3B82F6 !important;
        padding: 0 10px !important;
        font-size: 1.2em !important;
    }
    
    /* RÈGLE ULTRA-SPÉCIFIQUE : Alignement à gauche pour TOUT le contenu des messages IA */
    div[data-testid="stChatMessage"] *,
    div[data-testid="stChatMessage"] .content-area,
    div[data-testid="stChatMessage"] > div > div:last-child,
    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] div,
    div[data-testid="stChatMessage"] span,
    div[data-testid="stChatMessage"] h1,
    div[data-testid="stChatMessage"] h2,
    div[data-testid="stChatMessage"] h3,
    div[data-testid="stChatMessage"] h4,
    div[data-testid="stChatMessage"] h5,
    div[data-testid="stChatMessage"] h6,
    div[data-testid="stChatMessage"] ul,
    div[data-testid="stChatMessage"] ol,
    div[data-testid="stChatMessage"] li,
    div[data-testid="stChatMessage"] blockquote,
    div[data-testid="stChatMessage"] pre {
        text-align: left !important;
    }
    
    /* Tableaux alignés à gauche - EXACTEMENT comme export HTML */
    div[data-testid="stChatMessage"] table td,
    div[data-testid="stChatMessage"] table th {
        text-align: left !important;
    }
    
    /* En-têtes de tableaux alignés à gauche */
    div[data-testid="stChatMessage"] table th {
        color: #262730 !important;
        font-weight: 600 !important;
    }
    
    /* Garder l'alignement gauche pour les listes dans les messages assistant */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"]) ul,
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"]) ol,
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"]) li {
        text-align: left !important;
    }
    
    /* Centrer les tableaux dans les messages assistant */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"]) table {
        margin: 1rem auto !important;
    }
    
    /* Avatar premium avec effet 3D */
    div[data-testid^="chatAvatarIcon"] {
        width: 52px !important;
        height: 52px !important;
        min-width: 52px !important;
        min-height: 52px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 26px !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    div[data-testid^="chatAvatarIcon"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 30% 30%, 
            rgba(255, 255, 255, 0.8) 0%, 
            transparent 60%);
        opacity: 0.6;
        border-radius: 50%;
    }
    
    div[data-testid^="chatAvatarIcon"]:hover {
        transform: scale(1.15) rotate(5deg);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Avatar utilisateur avec effet premium */
    div[data-testid^="chatAvatarIcon-user"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%) !important;
        border: 3px solid rgba(255, 255, 255, 0.9) !important;
        box-shadow: 
            0 4px 15px rgba(59, 130, 246, 0.4),
            inset 0 1px 2px rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Avatar assistant avec effet sophistiqué */
    div[data-testid^="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #434343 0%, #000000 100%) !important;
        border: 3px solid rgba(255, 255, 255, 0.9) !important;
        box-shadow: 
            0 4px 15px rgba(0, 0, 0, 0.3),
            inset 0 -2px 4px rgba(0, 0, 0, 0.5),
            inset 0 1px 2px rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Avatar recherche avec effet brillant */
    div[data-testid^="chatAvatarIcon-search_result"] {
        background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important;
        border: 3px solid rgba(255, 255, 255, 0.9) !important;
        box-shadow: 
            0 4px 15px rgba(0, 201, 255, 0.4),
            inset 0 1px 2px rgba(255, 255, 255, 0.5) !important;
    }
    
    /* Texte du message - Typographie premium */
    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {
        font-family: 'Poppins', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 15px !important;
        line-height: 1.7 !important;
        font-weight: 400 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        text-rendering: optimizeLegibility !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
    }
    
    /* Texte utilisateur - Contraste élevé et lisibilité */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-user"]) p,
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] {
        color: #1e293b !important;
        font-weight: 500 !important;
        text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8) !important;
    }
    
    /* Texte assistant */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"]) p,
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"]) div[data-testid="stMarkdownContainer"] {
        color: #1F2937 !important;
    }
    
    /* Texte recherche */
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-search_result"]) p,
    div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-search_result"]) div[data-testid="stMarkdownContainer"] {
        color: #064E3B !important;
    }
    
    /* Styles pour les éléments markdown dans les messages */
    div[data-testid="stChatMessage"] h1,
    div[data-testid="stChatMessage"] h2,
    div[data-testid="stChatMessage"] h3 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    div[data-testid="stChatMessage"] ul,
    div[data-testid="stChatMessage"] ol {
        margin: 0.5rem 0 !important;
        padding-left: 1.5rem !important;
    }
    
    div[data-testid="stChatMessage"] li {
        margin: 0.25rem 0 !important;
    }
    
    /* Code blocks stylés */
    div[data-testid="stChatMessage"] code {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%) !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-family: 'Fira Code', 'Menlo', 'Monaco', 'Consolas', monospace !important;
        font-size: 13px !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    
    div[data-testid="stChatMessage"] pre {
        background-color: #1F2937 !important;
        color: #F9FAFB !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        overflow-x: auto !important;
        margin: 0.5rem 0 !important;
    }
    
    /* Métadonnées élégantes pour chaque message */
    .message-metadata {
        position: absolute;
        bottom: -22px;
        right: 25px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        color: #64748b;
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    div[data-testid="stChatMessage"]:hover .message-metadata {
        opacity: 1;
    }
    
    .message-time {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .message-time::before {
        content: '⏰';
        font-size: 12px;
    }
    
    /* Indicateur de statut */
    .message-status {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3);
    }
    
    /* Animations sophistiquées */
    @keyframes messageSlideIn {
        0% {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
            filter: blur(5px);
        }
        60% {
            opacity: 1;
            transform: translateY(-5px) scale(1.02);
            filter: blur(0);
        }
        100% {
            opacity: 1;
            transform: translateY(0) scale(1);
            filter: blur(0);
        }
    }
    
    @keyframes newMessagePulse {
        0% {
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
        }
        50% {
            box-shadow: 0 0 0 15px rgba(59, 130, 246, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
        }
    }
    
    /* Animation de frappe pour l'assistant */
    @keyframes typingIndicator {
        0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.7;
        }
        30% {
            transform: translateY(-10px);
            opacity: 1;
        }
    }
    
    /* Points de frappe */
    .typing-indicator {
        display: inline-flex;
        gap: 4px;
        padding: 0 10px;
    }
    
    .typing-indicator span {
        width: 8px;
        height: 8px;
        background: #6366f1;
        border-radius: 50%;
        animation: typingIndicator 1.4s infinite ease-in-out;
    }
    
    .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
    .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0; }
    
    /* Header premium sophistiqué */
    .main-header-premium {
        background: linear-gradient(135deg, 
            rgba(59, 130, 246, 0.1) 0%, 
            rgba(37, 99, 235, 0.1) 50%, 
            rgba(29, 78, 216, 0.1) 100%);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 30px;
        margin-bottom: 40px;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 
            0 20px 40px rgba(59, 130, 246, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.5);
    }
    
    .header-glow {
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, 
            rgba(59, 130, 246, 0.3) 0%, 
            transparent 70%);
        animation: headerGlow 8s ease-in-out infinite;
    }
    
    @keyframes headerGlow {
        0%, 100% { transform: rotate(0deg) scale(1); opacity: 0.5; }
        50% { transform: rotate(180deg) scale(1.1); opacity: 0.8; }
    }
    
    .header-content {
        position: relative;
        z-index: 1;
        display: flex;
        align-items: center;
        gap: 25px;
    }
    
    .header-icon-container {
        position: relative;
        width: 80px;
        height: 80px;
    }
    
    .header-icon {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        box-shadow: 
            0 10px 30px rgba(59, 130, 246, 0.4),
            inset 0 2px 4px rgba(255, 255, 255, 0.3);
        position: relative;
        z-index: 2;
    }
    
    .icon-ring {
        position: absolute;
        top: -5px;
        left: -5px;
        right: -5px;
        bottom: -5px;
        border: 2px solid rgba(59, 130, 246, 0.3);
        border-radius: 50%;
        animation: iconRing 3s linear infinite;
    }
    
    @keyframes iconRing {
        0% { transform: rotate(0deg) scale(1); opacity: 1; }
        50% { transform: rotate(180deg) scale(1.1); opacity: 0.5; }
        100% { transform: rotate(360deg) scale(1); opacity: 1; }
    }
    
    .header-title {
        font-family: 'Poppins', sans-serif !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .header-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #64748b;
        margin: 5px 0 !important;
    }
    
    .header-status {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 10px;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3);
        animation: statusPulse 2s ease-in-out infinite;
    }
    
    @keyframes statusPulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.8; }
    }
    
    .status-text {
        font-size: 0.875rem;
        color: #10b981;
        font-weight: 500;
    }
    
    /* Effet de brillance sur les messages */
    div[data-testid="stChatMessage"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(255, 255, 255, 0.2) 50%, 
            transparent 100%);
        transform: skewX(-20deg);
        transition: left 0.5s ease;
    }
    
    div[data-testid="stChatMessage"]:hover::before {
        left: 100%;
    }
    
    /* Scrollbar personnalisée */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 10px;
        border: 2px solid transparent;
        background-clip: padding-box;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
    }
    
    /* Responsive pour mobile et tablette */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 0.5rem !important;
        }
        
        div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-user"]) {
            margin-left: 5% !important;
            margin-right: 0 !important;
            max-width: 90% !important;
        }
        
        div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"]),
        div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-search_result"]) {
            margin-left: 0 !important;
            margin-right: 5% !important;
            max-width: 90% !important;
        }
        
        div[data-testid^="chatAvatarIcon"] {
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            min-height: 44px !important;
            font-size: 22px !important;
        }
        
        div[data-testid="stChatMessage"] > div {
            padding: 1rem 1.25rem !important;
        }
        
        .main-header-premium {
            padding: 20px !important;
            margin-bottom: 25px !important;
        }
        
        .header-content {
            flex-direction: column !important;
            text-align: center !important;
            gap: 15px !important;
        }
        
        .header-title {
            font-size: 1.5rem !important;
        }
        
        .header-icon-container {
            width: 60px !important;
            height: 60px !important;
        }
        
        .header-icon {
            width: 60px !important;
            height: 60px !important;
            font-size: 30px !important;
        }
    }
    
    /* Responsive pour très petits écrans */
    @media (max-width: 480px) {
        div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-user"]),
        div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-assistant"]),
        div[data-testid="stChatMessage"]:has(div[data-testid^="chatAvatarIcon-search_result"]) {
            margin-left: 2% !important;
            margin-right: 2% !important;
            max-width: 96% !important;
        }
        
        .header-title {
            font-size: 1.3rem !important;
        }
    }
    
    /* Scrollbar personnalisée pour les messages avec tableaux */
    div[data-testid="stChatMessage"]::-webkit-scrollbar {
        height: 8px !important;
        background-color: rgba(59, 130, 246, 0.1) !important;
        border-radius: 4px !important;
    }
    
    div[data-testid="stChatMessage"]::-webkit-scrollbar-thumb {
        background: linear-gradient(90deg, #3B82F6, #60A5FA) !important;
        border-radius: 4px !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stChatMessage"]::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(90deg, #2563EB, #3B82F6) !important;
        transform: scaleY(1.2) !important;
    }
    
    div[data-testid="stChatMessage"]::-webkit-scrollbar-track {
        background-color: rgba(0, 0, 0, 0.05) !important;
        border-radius: 4px !important;
    }
    
    /* Style pour Firefox */
    div[data-testid="stChatMessage"] {
        scrollbar-width: thin !important;
        scrollbar-color: #3B82F6 rgba(59, 130, 246, 0.1) !important;
    }
    
    </style>
    """, unsafe_allow_html=True)

    # Boucle d'affichage des messages
    for message in st.session_state.messages:
        role = message.get("role", "unknown")
        content = message.get("content", "*Message vide*")
        if role == "system": continue
        
        # Configuration des avatars améliorés
        if role == "user":
            avatar = "👤"
            avatar_class = "avatar-user"
        elif role == "assistant":
            avatar = "🏗️"
            avatar_class = "avatar-assistant"
        elif role == "search_result":
            avatar = "🔎"
            avatar_class = "avatar-search"
        else:
            avatar = "🤖"
            avatar_class = ""
        
        with st.chat_message(role, avatar=avatar):
            display_content = str(content) if not isinstance(content, str) else content
            st.markdown(display_content, unsafe_allow_html=False)

# --- Chat Input ---
# Style pour le chat input
st.markdown("""
<style>
div[data-testid="stChatInput"] {
    background-color: var(--secondary-background-color);
    border-top: 1px solid var(--border-color);
    padding: 0.5rem 1rem;
    box-shadow: 0 -2px 5px rgba(0,0,0,0.03);
    border-radius: 12px 12px 0 0;
    margin-top: 20px;
}

div[data-testid="stChatInput"] textarea {
    border-radius: 12px;
    border: 1px solid var(--border-color);
    background-color: var(--background-color);
    padding: 0.8rem 1rem;
    font-family: var(--font-family) !important;
    transition: all 0.3s;
    resize: none;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

div[data-testid="stChatInput"] textarea:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
    transform: translateY(-1px);
}

div[data-testid="stChatInput"] button {
    background-color: var(--primary-color) !important;
    border-radius: 12px !important;
    fill: white !important;
    padding: 0.7rem !important;
    box-shadow: var(--box-shadow-sm);
    transition: all 0.3s;
    border: none !important;
}

div[data-testid="stChatInput"] button:hover {
    background-color: var(--primary-color-darker) !important;
    transform: translateY(-2px);
    box-shadow: 0 3px 6px rgba(59, 130, 246, 0.2);
}

div[data-testid="stChatInput"] button:disabled {
    background-color: #9CA3AF !important;
    transform: none;
    box-shadow: none;
}
</style>
""", unsafe_allow_html=True)

prompt = st.chat_input("Posez votre question ou tapez /search [recherche web]...")

# --- Traitement du nouveau prompt ---
if prompt:
    user_msg = {"role": "user", "content": prompt, "id": datetime.now().isoformat()}
    st.session_state.messages.append(user_msg)
    save_current_conversation()
    if 'html_download_data' in st.session_state: del st.session_state.html_download_data
    if 'single_message_download' in st.session_state: del st.session_state.single_message_download
    if 'show_copy_content' in st.session_state: del st.session_state.show_copy_content
    st.rerun()

# --- LOGIQUE DE RÉPONSE / RECHERCHE / ANALYSE ---
action_to_process = None
if st.session_state.messages and 'expert_advisor' in st.session_state:
    last_message = st.session_state.messages[-1]
    msg_id = last_message.get("id", last_message.get("content")) # Use ID if available, else content hash (less reliable)
    if msg_id not in st.session_state.processed_messages: action_to_process = last_message

if action_to_process and action_to_process.get("role") == "user":
    msg_id = action_to_process.get("id", action_to_process.get("content"))
    st.session_state.processed_messages.add(msg_id)
    user_content = action_to_process.get("content", "")

    # Amélioration de la détection de commande search
    is_search_command = False
    search_query = ""

    if user_content.strip().lower().startswith("/search "):
        is_search_command = True
        search_query = user_content[len("/search "):].strip()
    elif user_content.strip().lower() == "/search":
        is_search_command = True
        search_query = ""  # Requête vide, à gérer

    # Commandes de modules supprimées - ne garder que /search



    # Récupérer les fichiers potentiellement à analyser DEPUIS l'état de session
    # 'files_to_analyze' est défini LORSQUE le bouton 'Analyser Fichiers' est cliqué
    files_for_analysis = st.session_state.get("files_to_analyze", [])
    # Vérifier si l'ID du message correspond à une action d'analyse ET s'il y a des fichiers stockés
    is_analysis_request = action_to_process.get("id", "").startswith("analyze_") and files_for_analysis

    if is_analysis_request:
        # --- Logique Analyse Fichiers ---
        with st.chat_message("assistant", avatar="🏗️"):
            with st.spinner("Analyse des documents..."):
                try:
                    # Les métadonnées de documents ne sont plus sauvegardées (module supprimé)

                    # Utiliser les fichiers stockés dans st.session_state.files_to_analyze
                    history_context = [m for m in st.session_state.messages[:-1] if m.get("role") != "system"]

                    # Appel à la fonction d'analyse
                    analysis_response, analysis_details = st.session_state.expert_advisor.analyze_documents(files_for_analysis, history_context)

                    # Les résultats d'analyse ne sont plus sauvegardés (module supprimé)

                    # Le logging des actions n'est plus disponible (module supprimé)

                    # Utiliser la nouvelle fonction d'affichage d'analyse
                    display_analysis_result(analysis_response, analysis_details)
                    
                    st.session_state.messages.append({"role": "assistant", "content": analysis_response})
                    st.success("Analyse terminée.")

                    # Nettoyer l'état après traitement pour éviter une nouvelle analyse au prochain rerun
                    if "files_to_analyze" in st.session_state:
                        del st.session_state.files_to_analyze

                except Exception as e:
                    error_msg = f"Erreur durant l'analyse des fichiers: {e}"
                    st.error(error_msg)
                    st.exception(e)
                    st.session_state.messages.append({"role": "assistant", "content": f"Désolé, une erreur s'est produite lors de l'analyse: {type(e).__name__}"})
                    # Nettoyer l'état même en cas d'erreur
                    if "files_to_analyze" in st.session_state:
                        del st.session_state.files_to_analyze

        save_current_conversation()
        st.rerun() # Rerun après l'analyse (succès ou échec)

    elif is_search_command:
        # --- Logique Recherche Web avec Cache ---
        query = search_query.strip()
        if not query:
            error_msg = "Commande `/search` vide. Veuillez fournir un terme de recherche."
            with st.chat_message("assistant", avatar="⚠️"):
                st.warning(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            save_current_conversation()
            st.rerun()
        else:
            # Ajouter un message d'attente
            with st.chat_message("assistant", avatar="🔎"):
                with st.spinner(f"Recherche web pour: '{query}'"):
                    try:
                        # NOUVEAU : Vérifier le cache d'abord
                        cached_result = None
                        if 'db_integration' in st.session_state and st.session_state.db_integration:
                            cached_result = st.session_state.db_integration.get_cached_search(query)

                        if cached_result:
                            # Utiliser le résultat en cache
                            st.info("✅ Résultat récupéré du cache (plus rapide)")
                            search_result = cached_result
                            
                            # Logger l'utilisation du cache
                            # Le tracking du cache de recherche n'est plus disponible
                        else:
                            # Nouvelle recherche
                            search_result = st.session_state.expert_advisor.perform_web_search(query)
                            
                            # Mettre en cache le résultat
                            if 'db_integration' in st.session_state and st.session_state.db_integration:
                                current_profile = st.session_state.expert_advisor.get_current_profile()
                                profile_name = current_profile.get('name', '') if current_profile else ''
                                
                                st.session_state.db_integration.cache_search_result(
                                    query=query,
                                    results=search_result,
                                    expert_profile=profile_name
                                )
                            
                            # Logger la nouvelle recherche
                            # Le tracking des recherches web n'est plus disponible
                        
                        # Style amélioré pour les résultats de recherche
                        st.markdown("""
                        <div class="search-result-container" style="animation: fadeIn 0.6s ease-out;">
                            <div style="display: flex; align-items: center; margin-bottom: 10px; color: #16a34a; font-weight: 600;">
                                <span style="margin-right: 8px; font-size: 1.2em;">🔎</span>
                                <span>Résultats de recherche</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(search_result)
                        
                        st.markdown("</div>", unsafe_allow_html=True)

                        # Ajouter le résultat aux messages
                        st.session_state.messages.append({
                            "role": "assistant", # Ou "search_result" si vous voulez un style distinct
                            "content": search_result,
                            "id": f"search_result_{datetime.now().isoformat()}"
                        })
                        save_current_conversation()
                        st.rerun() # Rerun après avoir ajouté le résultat

                    except Exception as e:
                        error_msg = f"Erreur lors de la recherche web: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Désolé, une erreur s'est produite lors de la recherche web: {type(e).__name__}",
                            "id": f"search_error_{datetime.now().isoformat()}"
                        })
                        save_current_conversation()
                        st.rerun() # Rerun même après erreur

    else: # Traiter comme chat normal - les commandes des modules supprimés ne sont plus supportées
        # --- Logique Réponse Claude ---
        with st.chat_message("assistant", avatar="🏗️"):
            placeholder = st.empty()
            with st.spinner("L'expert réfléchit..."):
                try:
                    # Préparer l'historique pour l'API Claude
                    # Exclure le dernier message utilisateur de l'historique passé à Claude
                    history_for_claude = [
                        msg for msg in st.session_state.messages[:-1]
                        if msg.get("role") in ["user", "assistant", "search_result"] # Filtrer les rôles valides
                    ]

                    response_content = st.session_state.expert_advisor.obtenir_reponse(user_content, history_for_claude)
                    
                    # Affichage amélioré de la réponse
                    placeholder.markdown("""
                    <div class="assistant-response" style="animation: fadeIn 0.6s ease-out;">
                    """, unsafe_allow_html=True)
                    
                    placeholder.markdown(response_content, unsafe_allow_html=False)
                    
                    placeholder.markdown("</div>", unsafe_allow_html=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response_content})
                    save_current_conversation()
                    st.rerun() # Rerun après la réponse de Claude

                except Exception as e:
                    error_msg = f"Erreur lors de l'obtention de la réponse de Claude: {e}"
                    print(error_msg)
                    st.exception(e)
                    placeholder.error(f"Désolé, une erreur technique s'est produite avec l'IA ({type(e).__name__}).")
                    st.session_state.messages.append({"role": "assistant", "content": f"Erreur technique avec l'IA ({type(e).__name__})."})
                    save_current_conversation()
                    st.rerun() # Rerun même après erreur

# --- Footer --- 
st.markdown("""
<div class="footer-container">
    <div class="copyright">© 2025 EXPERTS IA - Développé par Sylvain Leduc</div>
</div>
""", unsafe_allow_html=True)