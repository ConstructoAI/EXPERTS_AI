#!/usr/bin/env python3
"""
Script de démarrage optimisé pour Render
EXPERTS IA - Plateforme d'experts en construction
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

def setup_environment():
    """Configure l'environnement pour Render."""
    # Port automatique de Render
    port = os.environ.get('PORT', '8501')
    
    # Configurer les variables par défaut si non définies
    defaults = {
        'LOG_LEVEL': 'INFO',
        'MAX_FILE_SIZE_MB': '50',
        'ENABLE_DEBUG': 'false',
        'ENABLE_SECURITY_LOGGING': 'true',
        'MAX_LOGIN_ATTEMPTS': '5',
        'LOCKOUT_DURATION': '30'
    }
    
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value
    
    print(f"🚀 Démarrage EXPERTS IA sur le port {port}")
    print(f"📊 Niveau de log: {os.environ.get('LOG_LEVEL')}")
    print(f"🔒 Sécurité: {os.environ.get('ENABLE_SECURITY_LOGGING')}")
    
    return port

def validate_critical_config():
    """Valide la configuration critique."""
    critical_vars = ['ANTHROPIC_API_KEY', 'APP_PASSWORD']
    missing = []
    
    for var in critical_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print(f"❌ ERREUR CRITIQUE: Variables manquantes: {', '.join(missing)}")
        print("💡 Configurez ces variables dans le dashboard Render")
        sys.exit(1)
    
    print("✅ Configuration critique validée")

def start_streamlit(port):
    """Démarre Streamlit avec la configuration optimale."""
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'true',
        '--server.maxUploadSize', os.environ.get('MAX_FILE_SIZE_MB', '50'),
        '--browser.gatherUsageStats', 'false',
        '--theme.base', 'light'
    ]
    
    print(f"🏃 Commande: {' '.join(cmd)}")
    
    # Gestion des signaux pour arrêt propre
    def signal_handler(sig, frame):
        print('\n🛑 Arrêt demandé...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Démarrer Streamlit
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print('\n🛑 Arrêt par Ctrl+C')
        sys.exit(0)

def main():
    """Fonction principale."""
    print("=" * 50)
    print("🏗️  EXPERTS IA - PLATEFORME SÉCURISÉE")
    print("   60+ Experts en Construction du Québec")
    print("=" * 50)
    
    # Vérifier que nous sommes dans le bon répertoire
    if not Path('app.py').exists():
        print("❌ ERREUR: app.py non trouvé dans le répertoire courant")
        sys.exit(1)
    
    # Configuration
    port = setup_environment()
    validate_critical_config()
    
    # Vérifier les profils
    profiles_dir = Path('profiles')
    if profiles_dir.exists():
        profile_count = len(list(profiles_dir.glob('*.txt')))
        print(f"👥 {profile_count} profils d'experts chargés")
    else:
        print("⚠️ Dossier profiles non trouvé")
    
    print("🚀 Démarrage de l'application...")
    start_streamlit(port)

if __name__ == "__main__":
    main()