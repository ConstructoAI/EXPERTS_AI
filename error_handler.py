"""
Module de gestion d'erreurs avancée pour EXPERTS IA
Logging, notifications et récupération d'erreurs
"""

import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path

# Configuration du logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Logger principal
logger = logging.getLogger("EXPERTS_IA")
logger.setLevel(logging.DEBUG)

# Format de log
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Handler fichier (tous les logs)
file_handler = logging.FileHandler(
    LOG_DIR / f"experts_ia_{datetime.now().strftime('%Y%m%d')}.log",
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler fichier (erreurs seulement)
error_handler = logging.FileHandler(
    LOG_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.log",
    encoding='utf-8'
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

# Handler console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class ExpertsIAError(Exception):
    """Exception de base pour EXPERTS IA"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class APIError(ExpertsIAError):
    """Erreur liée à l'API Anthropic"""
    pass


class DatabaseError(ExpertsIAError):
    """Erreur liée à la base de données"""
    pass


class ValidationError(ExpertsIAError):
    """Erreur de validation des données"""
    pass


class ExtractionError(ExpertsIAError):
    """Erreur lors de l'extraction de données"""
    pass


def log_error(error, context=None):
    """
    Log une erreur avec contexte complet

    Args:
        error: L'exception ou le message d'erreur
        context: Dict avec informations contextuelles
    """
    context = context or {}

    error_info = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context
    }

    if isinstance(error, Exception):
        error_info['traceback'] = traceback.format_exc()

    logger.error(f"ERREUR: {error_info}")

    return error_info


def safe_execute(func, *args, fallback=None, error_message="Erreur lors de l'exécution", **kwargs):
    """
    Exécute une fonction avec gestion d'erreur robuste

    Args:
        func: Fonction à exécuter
        *args: Arguments positionnels
        fallback: Valeur de retour en cas d'erreur
        error_message: Message d'erreur personnalisé
        **kwargs: Arguments nommés

    Returns:
        Résultat de la fonction ou fallback en cas d'erreur
    """
    try:
        result = func(*args, **kwargs)
        logger.debug(f"✅ {func.__name__} exécuté avec succès")
        return result
    except Exception as e:
        log_error(e, context={
            'function': func.__name__,
            'args': str(args)[:200],
            'kwargs': str(kwargs)[:200]
        })
        logger.warning(f"⚠️ {error_message}: {e}")
        return fallback


def validate_api_key(api_key):
    """
    Valide une clé API Anthropic

    Args:
        api_key: Clé API à valider

    Returns:
        bool: True si valide

    Raises:
        ValidationError: Si invalide
    """
    if not api_key:
        raise ValidationError("Clé API manquante", error_code="API_KEY_MISSING")

    if not isinstance(api_key, str):
        raise ValidationError("Clé API doit être une chaîne", error_code="API_KEY_INVALID_TYPE")

    if not api_key.startswith('sk-'):
        raise ValidationError("Format de clé API invalide", error_code="API_KEY_INVALID_FORMAT")

    if len(api_key) < 20:
        raise ValidationError("Clé API trop courte", error_code="API_KEY_TOO_SHORT")

    logger.debug("✅ Clé API validée")
    return True


def validate_soumission_data(data):
    """
    Valide les données d'une soumission

    Args:
        data: Dict de données de soumission

    Returns:
        bool: True si valide

    Raises:
        ValidationError: Si invalide
    """
    required_fields = ['client', 'projet', 'travaux', 'recapitulatif']

    for field in required_fields:
        if field not in data:
            raise ValidationError(
                f"Champ requis manquant: {field}",
                error_code="MISSING_FIELD",
                details={'field': field}
            )

    # Valider le récapitulatif
    recap = data.get('recapitulatif', {})
    if recap.get('investissement_total', 0) <= 0:
        logger.warning("⚠️ Montant total de soumission = 0")

    logger.debug("✅ Données de soumission validées")
    return True


def handle_api_error(error):
    """
    Gère les erreurs API Anthropic de manière intelligente

    Args:
        error: Exception API

    Returns:
        dict: Message d'erreur formaté pour l'utilisateur
    """
    error_str = str(error).lower()

    if 'rate limit' in error_str or '429' in error_str:
        return {
            'type': 'rate_limit',
            'user_message': "⏱️ Trop de requêtes. Veuillez patienter quelques secondes.",
            'retry_after': 5,
            'recoverable': True
        }

    elif 'authentication' in error_str or '401' in error_str:
        return {
            'type': 'auth_error',
            'user_message': "🔑 Clé API invalide. Vérifiez votre clé Anthropic.",
            'recoverable': False
        }

    elif 'timeout' in error_str:
        return {
            'type': 'timeout',
            'user_message': "⏰ Délai d'attente dépassé. Réessayez.",
            'recoverable': True
        }

    elif 'network' in error_str or 'connection' in error_str:
        return {
            'type': 'network_error',
            'user_message': "📡 Erreur de connexion. Vérifiez votre internet.",
            'recoverable': True
        }

    else:
        return {
            'type': 'unknown_error',
            'user_message': f"❌ Erreur API: {str(error)[:100]}",
            'recoverable': False
        }


def retry_with_backoff(func, max_retries=3, backoff_factor=2, *args, **kwargs):
    """
    Réessaie une fonction avec délai exponentiel

    Args:
        func: Fonction à exécuter
        max_retries: Nombre maximum de tentatives
        backoff_factor: Facteur multiplicateur du délai
        *args, **kwargs: Arguments de la fonction

    Returns:
        Résultat de la fonction

    Raises:
        Exception: Si toutes les tentatives échouent
    """
    import time

    last_error = None

    for attempt in range(max_retries):
        try:
            logger.debug(f"Tentative {attempt + 1}/{max_retries} pour {func.__name__}")
            result = func(*args, **kwargs)
            logger.info(f"✅ {func.__name__} réussi après {attempt + 1} tentative(s)")
            return result

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = backoff_factor ** attempt
                logger.warning(f"⚠️ Échec tentative {attempt + 1}, réessai dans {delay}s: {e}")
                time.sleep(delay)
            else:
                logger.error(f"❌ Toutes les tentatives ont échoué pour {func.__name__}")

    raise last_error


# Initialisation
logger.info("=" * 80)
logger.info("EXPERTS IA - Démarrage du système de logging")
logger.info("=" * 80)
