# security_utils.py
# Utilitaires de sécurité pour EXPERTS IA

import os
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
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
        # Obtenir l'IP depuis Streamlit (approximative)
        user_info = f"Session: {st.session_state.get('session_id', 'unknown')}"
        message = f"{event_type} - {details} - {user_info}"
        
        if level.upper() == "CRITICAL":
            SECURITY_LOGGER.critical(message)
        elif level.upper() == "ERROR":
            SECURITY_LOGGER.error(message)
        elif level.upper() == "WARNING":
            SECURITY_LOGGER.warning(message)
        else:
            SECURITY_LOGGER.info(message)

class LoginAttemptTracker:
    """Tracker des tentatives de connexion."""
    
    def __init__(self):
        self.max_attempts = int(os.environ.get("MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration = int(os.environ.get("LOCKOUT_DURATION", "30"))  # minutes
        
        # Stockage en session state
        if 'login_attempts' not in st.session_state:
            st.session_state.login_attempts = {}
        if 'lockout_until' not in st.session_state:
            st.session_state.lockout_until = {}
    
    def get_session_id(self) -> str:
        """Obtient un identifiant de session unique."""
        if 'session_id' not in st.session_state:
            # Créer un ID unique basé sur l'heure et un hash
            timestamp = str(time.time())
            st.session_state.session_id = hashlib.md5(timestamp.encode()).hexdigest()[:12]
        return st.session_state.session_id
    
    def is_locked_out(self) -> bool:
        """Vérifie si la session est bloquée."""
        session_id = self.get_session_id()
        
        if session_id in st.session_state.lockout_until:
            lockout_time = st.session_state.lockout_until[session_id]
            if datetime.now() < lockout_time:
                return True
            else:
                # Le blocage est expiré
                del st.session_state.lockout_until[session_id]
                if session_id in st.session_state.login_attempts:
                    del st.session_state.login_attempts[session_id]
        
        return False
    
    def record_failed_attempt(self):
        """Enregistre une tentative de connexion échouée."""
        session_id = self.get_session_id()
        
        if session_id not in st.session_state.login_attempts:
            st.session_state.login_attempts[session_id] = 0
        
        st.session_state.login_attempts[session_id] += 1
        attempts = st.session_state.login_attempts[session_id]
        
        log_security_event(
            "FAILED_LOGIN_ATTEMPT", 
            f"Tentative #{attempts} pour session {session_id}",
            "WARNING"
        )
        
        if attempts >= self.max_attempts:
            # Bloquer la session
            lockout_until = datetime.now() + timedelta(minutes=self.lockout_duration)
            st.session_state.lockout_until[session_id] = lockout_until
            
            log_security_event(
                "SESSION_LOCKED", 
                f"Session {session_id} bloquée jusqu'à {lockout_until}",
                "ERROR"
            )
    
    def record_successful_login(self):
        """Enregistre une connexion réussie."""
        session_id = self.get_session_id()
        
        # Nettoyer les tentatives échouées
        if session_id in st.session_state.login_attempts:
            del st.session_state.login_attempts[session_id]
        if session_id in st.session_state.lockout_until:
            del st.session_state.lockout_until[session_id]
        
        log_security_event(
            "SUCCESSFUL_LOGIN", 
            f"Connexion réussie pour session {session_id}",
            "INFO"
        )
    
    def get_remaining_attempts(self) -> int:
        """Retourne le nombre de tentatives restantes."""
        session_id = self.get_session_id()
        attempts = st.session_state.login_attempts.get(session_id, 0)
        return max(0, self.max_attempts - attempts)
    
    def get_lockout_time_remaining(self) -> Optional[timedelta]:
        """Retourne le temps de blocage restant."""
        session_id = self.get_session_id()
        
        if session_id in st.session_state.lockout_until:
            lockout_until = st.session_state.lockout_until[session_id]
            remaining = lockout_until - datetime.now()
            if remaining > timedelta(0):
                return remaining
        
        return None

def validate_environment_variables() -> List[str]:
    """Valide les variables d'environnement critiques."""
    missing_vars = []
    critical_vars = ["ANTHROPIC_API_KEY", "APP_PASSWORD"]
    
    for var in critical_vars:
        if not os.environ.get(var) and not st.secrets.get(var, None):
            missing_vars.append(var)
    
    if missing_vars:
        log_security_event(
            "MISSING_CONFIG",
            f"Variables critiques manquantes: {', '.join(missing_vars)}",
            "CRITICAL"
        )
    
    return missing_vars

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