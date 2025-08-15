# app.py - Version avec saisie de clé API (SANS authentification)
import streamlit as st
import os
import io
import html
import markdown
import time
from datetime import datetime
from dotenv import load_dotenv

# Importer les classes logiques et le gestionnaire de conversation
try:
    from expert_logic import ExpertAdvisor, ExpertProfileManager
    from conversation_manager import ConversationManager
    from security_utils import log_security_event, check_rate_limiting, sanitize_input
except ImportError as e:
    st.error(f"Erreur d'importation des modules locaux: {e}")
    st.error("Assurez-vous que tous les fichiers requis existent dans le même dossier.")
    st.stop()

# Configuration de la page
st.set_page_config(
    page_title="EXPERTS IA",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger CSS
def local_css(file_name):
    """Charge les styles CSS depuis un fichier local."""
    try:
        css_path = os.path.join(os.path.dirname(__file__), file_name)
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Fichier CSS '{file_name}' non trouvé.")
    except Exception as e:
        st.error(f"Erreur CSS '{file_name}': {e}")

# Helper Function pour lire le CSS pour l'intégration HTML
@st.cache_data
def load_css_content(file_name):
    """Charge le contenu brut d'un fichier CSS."""
    try:
        css_path = os.path.join(os.path.dirname(__file__), file_name)
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""
    except Exception:
        return ""

# Charger le CSS
local_css("style.css")

def validate_api_key(api_key):
    """Valide le format de la clé API."""
    if not api_key:
        return False, "Clé API requise"
    
    # Vérifier le format de base
    if not api_key.startswith('sk-ant-api03-'):
        return False, "La clé doit commencer par 'sk-ant-api03-'"
    
    # Vérifier la longueur approximative
    if len(api_key) < 100:
        return False, "Clé API trop courte"
    
    return True, "Clé API valide"

def handle_api_key():
    """Gère la saisie et validation de la clé API Claude."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 Configuration API Claude")
    
    # Champ de saisie de la clé API
    api_key = st.sidebar.text_input(
        "Clé API Claude:",
        type="password",
        placeholder="sk-ant-api03-...",
        help="Collez votre clé API Claude d'Anthropic ici. Elle commence par 'sk-ant-api03-'",
        key="anthropic_api_key_input"
    )
    
    # Boutons d'aide
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("❓ Comment obtenir ?", key="help_api"):
            st.sidebar.info("""
            **Étapes simples :**
            1. 🌐 https://claude.ai/
            2. 📝 Créer compte gratuit
            3. 💳 Ajouter 20$ crédits
            4. 🔑 Générer clé API
            5. 📋 Copier/coller ici
            """)
    
    with col2:
        if st.button("🔄 Tester", key="test_api") and api_key:
            is_valid, message = validate_api_key(api_key)
            if is_valid:
                st.sidebar.success("✅ " + message)
            else:
                st.sidebar.error("❌ " + message)
    
    return api_key

def show_welcome_screen():
    """Affiche l'écran d'accueil sans clé API."""
    st.markdown("""
    <div class="main-header">
        <h1>🏗️ EXPERTS IA</h1>
        <p>60+ Experts en Construction du Québec</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    ### 👋 Bienvenue sur EXPERTS IA !
    
    Pour commencer, configurez votre clé API Claude dans la barre latérale ←
    
    **Étapes rapides :**
    1. 📝 Créez un compte sur https://claude.ai/
    2. 💳 Ajoutez 20$ USD de crédits
    3. 🔑 Générez votre clé API
    4. 📋 Collez-la dans le champ "Clé API Claude"
    
    **Vos avantages :**
    - ✅ Utilisez vos propres crédits
    - ✅ Contrôle total de l'usage
    - ✅ Pas de limite de temps
    - ✅ Confidentialité maximale
    """)
    
    # Afficher aperçu des experts
    st.markdown("### 🎯 Aperçu des Experts Disponibles")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **🏗️ Entrepreneur Général**
        - Estimations détaillées 2025
        - Gestion de projets
        - Coordination métiers
        - Calculs heures/pi²
        """)
    
    with col2:
        st.markdown("""
        **⚡ Électricien CMEQ**
        - Code électrique QC
        - 500+ produits/prix
        - Installations certifiées
        - Normes Hydro-Québec
        """)
    
    with col3:
        st.markdown("""
        **🏠 Architecte OAQ**
        - Design créatif
        - Conformité codes
        - Plans détaillés
        - Efficacité énergétique
        """)
    
    st.markdown("### 🔍 Fonctionnalités Avancées")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **📄 Analyse de Documents**
        - PDF, Word, Excel, Images
        - Plans de construction
        - Devis techniques
        - Photos de chantier
        """)
    
    with col2:
        st.markdown("""
        **🔍 Recherche Web**
        - Tapez `/search votre requête`
        - Prix actualisés matériaux
        - Réglementations récentes
        - Innovations techniques
        """)

def initialize_app_components(api_key):
    """Initialise les composants de l'application avec la clé API."""
    try:
        # Initialiser l'expert advisor avec la clé fournie
        if 'expert_advisor' not in st.session_state or st.session_state.get('current_api_key') != api_key:
            st.session_state.expert_advisor = ExpertAdvisor(api_key=api_key)
            st.session_state.current_api_key = api_key
        
        # Initialiser le gestionnaire de conversation
        if 'conversation_manager' not in st.session_state:
            st.session_state.conversation_manager = ConversationManager()
        
        # Initialiser les messages si nécessaire
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # Initialiser l'ID de conversation
        if 'current_conversation_id' not in st.session_state:
            st.session_state.current_conversation_id = None
        
        return True, "Initialisation réussie"
        
    except Exception as e:
        return False, f"Erreur d'initialisation: {str(e)}"

def show_sidebar():
    """Affiche la sidebar avec sélection d'expert et historique."""
    # Logo et titre
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #3B82F6; margin: 0;">🏗️ EXPERTS IA</h2>
        <p style="color: #6B7280; margin: 0.5rem 0 0 0;">Construction Québec</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Sélection du profil expert
    st.sidebar.markdown("### 👤 Profil Expert")
    
    # Obtenir la liste des profils disponibles
    available_profiles = st.session_state.expert_advisor.profile_manager.get_profile_names()
    
    # Sélecteur de profil
    selected_profile = st.sidebar.selectbox(
        "Choisissez votre expert:",
        options=available_profiles,
        index=available_profiles.index("Entrepreneur Général") if "Entrepreneur Général" in available_profiles else 0,
        key="selected_profile",
        help="Sélectionnez l'expert le plus adapté à votre question"
    )
    
    # Stocker le profil sélectionné
    if 'selected_profile_name' not in st.session_state:
        st.session_state.selected_profile_name = selected_profile
    elif st.session_state.selected_profile_name != selected_profile:
        st.session_state.selected_profile_name = selected_profile
        st.sidebar.success(f"✅ Expert changé: **{selected_profile}**")
    
    st.sidebar.markdown("---")
    
    # Section upload de fichiers
    st.sidebar.markdown("### 📄 Analyse de Fichiers")
    
    uploaded_files = st.sidebar.file_uploader(
        "Ajouter des documents:",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt', 'png', 'jpg', 'jpeg'],
        help="PDF, Word, Excel, images supportés"
    )
    
    # Afficher les fichiers uploadés
    if uploaded_files:
        st.sidebar.write(f"📁 **{len(uploaded_files)} fichier(s) chargé(s)**")
        for file in uploaded_files:
            st.sidebar.write(f"• {file.name}")
    
    st.sidebar.markdown("---")
    
    # Gestion des conversations
    st.sidebar.markdown("### 💬 Conversations")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("➕ Nouveau", key="new_conversation", help="Démarrer une nouvelle conversation"):
            st.session_state.messages = []
            st.session_state.current_conversation_id = None
            st.rerun()
    
    with col2:
        if st.button("💾 Sauver", key="save_conversation", help="Sauvegarder la conversation actuelle"):
            if st.session_state.messages:
                try:
                    conversation_id = st.session_state.conversation_manager.save_conversation(
                        st.session_state.get('current_conversation_id'),
                        st.session_state.messages
                    )
                    st.session_state.current_conversation_id = conversation_id
                    st.sidebar.success("✅ Conversation sauvegardée")
                except Exception as e:
                    st.sidebar.error(f"❌ Erreur sauvegarde: {str(e)}")
    
    # Historique des conversations
    try:
        conversations = st.session_state.conversation_manager.get_all_conversations()
        if conversations:
            st.sidebar.markdown("#### 📚 Historique")
            for conv in conversations[:5]:  # Limiter à 5 conversations récentes
                col1, col2 = st.sidebar.columns([3, 1])
                with col1:
                    if st.button(conv['name'][:25] + "...", key=f"load_{conv['id']}", help=f"Charger: {conv['name']}"):
                        try:
                            messages = st.session_state.conversation_manager.load_conversation(conv['id'])
                            st.session_state.messages = messages
                            st.session_state.current_conversation_id = conv['id']
                            st.rerun()
                        except Exception as e:
                            st.sidebar.error(f"❌ Erreur chargement: {str(e)}")
                
                with col2:
                    if st.button("🗑️", key=f"delete_{conv['id']}", help="Supprimer"):
                        try:
                            st.session_state.conversation_manager.delete_conversation(conv['id'])
                            st.rerun()
                        except Exception as e:
                            st.sidebar.error(f"❌ Erreur suppression: {str(e)}")
    except Exception as e:
        st.sidebar.error(f"❌ Erreur historique: {str(e)}")
    
    return uploaded_files

def export_conversation_html():
    """Exporte la conversation actuelle en HTML."""
    if not st.session_state.messages:
        st.warning("Aucune conversation à exporter")
        return
    
    try:
        # CSS intégré
        css_content = load_css_content("style.css")
        
        # Générer le HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consultation EXPERTS IA - {datetime.now().strftime('%d/%m/%Y %H:%M')}</title>
    <style>
        {css_content}
        body {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
        .export-header {{ text-align: center; margin-bottom: 2rem; }}
        .message {{ margin-bottom: 1.5rem; padding: 1rem; border-radius: 8px; }}
        .user-message {{ background: #f0f9ff; border-left: 4px solid #3b82f6; }}
        .assistant-message {{ background: #f9fafb; border-left: 4px solid #10b981; }}
    </style>
</head>
<body>
    <div class="export-header">
        <h1>🏗️ EXPERTS IA - Consultation</h1>
        <p><strong>Expert consulté:</strong> {st.session_state.get('selected_profile_name', 'Non spécifié')}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
        <hr>
    </div>
    
    <div class="conversation">
"""
        
        for message in st.session_state.messages:
            role = message.get('role', 'user')
            content = html.escape(message.get('content', ''))
            
            if role == 'user':
                html_content += f"""
        <div class="message user-message">
            <h4>👤 Question:</h4>
            <p>{content}</p>
        </div>
"""
            elif role == 'assistant':
                html_content += f"""
        <div class="message assistant-message">
            <h4>🤖 {st.session_state.get('selected_profile_name', 'Expert')}:</h4>
            <div>{markdown.markdown(content)}</div>
        </div>
"""
        
        html_content += """
    </div>
    
    <div style="text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #e5e7eb;">
        <p style="color: #6b7280;">Généré par EXPERTS IA - 60+ Experts Construction Québec</p>
        <p style="color: #6b7280; font-size: 0.9rem;">www.experts-ia.ca</p>
    </div>
</body>
</html>
"""
        
        # Proposer le téléchargement
        st.download_button(
            label="📥 Télécharger la consultation (HTML)",
            data=html_content,
            file_name=f"consultation_experts_ia_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            help="Télécharge un rapport HTML professionnel de votre consultation"
        )
        
    except Exception as e:
        st.error(f"❌ Erreur lors de l'export: {str(e)}")

def main():
    """Fonction principale de l'application."""
    
    # Gestion de la clé API
    api_key = handle_api_key()
    
    # Vérifier que la clé API est fournie
    if not api_key:
        show_welcome_screen()
        return
    
    # Valider le format de la clé
    is_valid, message = validate_api_key(api_key)
    if not is_valid:
        st.sidebar.error(f"❌ {message}")
        show_welcome_screen()
        return
    
    # Initialiser les composants de l'application
    success, init_message = initialize_app_components(api_key)
    if not success:
        st.sidebar.error(f"❌ {init_message}")
        return
    
    # Afficher confirmation d'initialisation
    st.sidebar.success("✅ EXPERTS IA initialisé")
    
    # Afficher la sidebar
    uploaded_files = show_sidebar()
    
    # Interface principale
    st.markdown("""
    <div class="main-header">
        <h1>🏗️ EXPERTS IA</h1>
        <p>60+ Experts en Construction du Québec - Alimenté par Claude</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Bouton d'export si messages existent
    if st.session_state.messages:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            export_conversation_html()
        with col3:
            if st.button("🔄 Nouvelle consultation", help="Effacer la conversation et recommencer"):
                st.session_state.messages = []
                st.session_state.current_conversation_id = None
                st.rerun()
    
    # Afficher les messages de la conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Interface de chat
    if prompt := st.chat_input("Posez votre question à l'expert..."):
        # Limiter le taux de requêtes
        if not check_rate_limiting():
            st.error("⏱️ Trop de requêtes. Veuillez patienter une minute.")
            return
        
        # Nettoyer l'entrée utilisateur
        prompt = sanitize_input(prompt)
        
        # Ajouter le message de l'utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Afficher le message de l'utilisateur
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Générer la réponse de l'assistant
        with st.chat_message("assistant"):
            with st.spinner("🤔 L'expert analyse votre question..."):
                try:
                    # Préparer l'historique pour Claude (exclure le dernier message utilisateur)
                    history_for_claude = [
                        msg for msg in st.session_state.messages[:-1]
                        if msg.get("role") in ["user", "assistant", "search_result"]
                    ]
                    
                    # Obtenir la réponse
                    if uploaded_files:
                        # Avec analyse de fichiers
                        response_content = st.session_state.expert_advisor.analyze_documents(
                            uploaded_files, history_for_claude
                        )
                    else:
                        # Sans fichiers
                        response_content = st.session_state.expert_advisor.obtenir_reponse(
                            prompt, history_for_claude
                        )
                    
                    # Afficher la réponse
                    st.markdown(response_content)
                    
                    # Ajouter la réponse aux messages
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response_content
                    })
                    
                except Exception as e:
                    error_message = f"❌ Erreur lors de la consultation de l'expert: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_message
                    })
    
    # Instructions d'utilisation
    if not st.session_state.messages:
        st.info("""
        💡 **Comment utiliser EXPERTS IA :**
        
        1. **Sélectionnez votre expert** dans la barre latérale selon votre besoin
        2. **Uploadez vos documents** (optionnel) : plans, devis, photos...
        3. **Posez votre question** dans le chat ci-dessous
        4. **Obtenez une expertise professionnelle** adaptée à votre profil d'expert
        
        **Commandes spéciales :**
        - Tapez `/search votre recherche` pour une recherche web spécialisée
        - Utilisez le bouton "💾 Sauver" pour conserver vos conversations
        - Exportez vos consultations en HTML professionnel
        """)

if __name__ == "__main__":
    main()