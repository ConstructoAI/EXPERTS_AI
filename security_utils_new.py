# security_utils.py - Version simplifiée (sans authentification)
# Utilitaires de sécurité pour EXPERTS IA

import os
import logging
import time
from datetime import datetime, timedelta
from typing import List
import streamlit as st

# Configuration du logging de sécurité
def setup_security_logging():
    """Configure les logs de sécurité."""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    enable_security_logging = os.environ.get("ENABLE_SECURITY_LOGGING", "true").lower() == "true"
    
    if not enable_security_logging:
        return None
    
    # Créer le logger de sécurité
    security_logger = logging.getLogger("EXPERTS_IA_SECURITY")
    security_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Handler pour fichier
    if not security_logger.handlers:
        file_handler = logging.FileHandler("security.log", encoding="utf-8")
        file_handler.setLevel(logging.WARNING)
        
        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        security_logger.addHandler(file_handler)
        security_logger.addHandler(console_handler)
    
    return security_logger

# Logger de sécurité global
SECURITY_LOGGER = setup_security_logging()

def log_security_event(event_type: str, details: str, level: str = "WARNING"):
    """Log un événement de sécurité."""
    if SECURITY_LOGGER:
        # Obtenir info session basique
        session_info = f"Session actuelle"
        message = f"{event_type} - {details} - {session_info}"
        
        if level.upper() == "CRITICAL":
            SECURITY_LOGGER.critical(message)
        elif level.upper() == "ERROR":
            SECURITY_LOGGER.error(message)
        elif level.upper() == "WARNING":
            SECURITY_LOGGER.warning(message)
        else:
            SECURITY_LOGGER.info(message)

def sanitize_input(text: str) -> str:
    """Nettoie et sanitise les entrées utilisateur."""
    if not isinstance(text, str):
        return str(text)
    
    # Supprimer les caractères de contrôle dangereux
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\t'])
    
    # Limiter la longueur
    max_length = 10000
    if len(sanitized) > max_length:
        log_security_event(
            "INPUT_TOO_LONG",
            f"Entrée tronquée: {len(text)} -> {max_length} caractères",
            "WARNING"
        )
        sanitized = sanitized[:max_length]
    
    return sanitized

def check_rate_limiting() -> bool:
    """Vérifie les limites de taux d'utilisation."""
    if 'requests_timestamp' not in st.session_state:
        st.session_state.requests_timestamp = []
    
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)
    
    # Nettoyer les anciennes requêtes
    st.session_state.requests_timestamp = [
        timestamp for timestamp in st.session_state.requests_timestamp 
        if timestamp > minute_ago
    ]
    
    # Vérifier la limite (30 requêtes par minute)
    max_requests_per_minute = 30
    if len(st.session_state.requests_timestamp) >= max_requests_per_minute:
        log_security_event(
            "RATE_LIMIT_EXCEEDED",
            f"Limite de {max_requests_per_minute} req/min dépassée",
            "WARNING"
        )
        return False
    
    # Enregistrer cette requête
    st.session_state.requests_timestamp.append(now)
    return True

def validate_environment_variables() -> List[str]:
    """Valide les variables d'environnement de base."""
    missing_vars = []
    basic_vars = ["LOG_LEVEL"]  # Variables de base seulement
    
    for var in basic_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        log_security_event(
            "MISSING_CONFIG",
            f"Variables basiques manquantes: {', '.join(missing_vars)}",
            "WARNING"
        )
    
    return missing_vars

def mask_sensitive_data(data: str, patterns: List[str] = None) -> str:
    """Masque les données sensibles dans les logs."""
    if not patterns:
        patterns = [
            r'sk-ant-api\d{2}-[A-Za-z0-9_-]{95}',  # Clés API Anthropic
            r'[A-Za-z0-9]{32,}',  # Clés génériques longues
            r'\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b',  # Numéros de carte
        ]
    
    import re
    masked = data
    for pattern in patterns:
        masked = re.sub(pattern, "***MASKED***", masked)
    
    return masked