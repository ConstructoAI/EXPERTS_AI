"""
Styles CSS centralisés pour tous les modules EXPERTS_AI
Utilise les mêmes couleurs que style.css
"""

def get_module_css():
    """Retourne le CSS standardisé pour tous les modules"""
    return """
    <style>
        /* === VARIABLES CSS (identiques à style.css) === */
        :root {
            /* Couleurs principales */
            --primary-color: #3B82F6;
            --primary-color-light: #93C5FD;
            --primary-color-lighter: #DBEAFE;
            --primary-color-darker: #2563EB;
            --primary-color-darkest: #1D4ED8;

            /* Couleurs boutons */
            --button-color: #1F2937;
            --button-color-light: #374151;
            --button-color-dark: #111827;

            /* Backgrounds */
            --background-color: #FAFBFF;
            --secondary-background: #F8FAFF;
            --card-background: #F5F8FF;
            --content-background: #FFFFFF;

            /* Texte */
            --text-color: #1F2937;
            --text-color-light: #6B7280;
            --text-color-muted: #9CA3AF;

            /* Bordures */
            --border-color: #E5E7EB;
            --border-color-light: #F3F4F6;
            --border-color-blue: #DBEAFE;

            /* Couleurs projet */
            --project-success: #22C55E;
            --project-warning: #F59E0B;
            --project-danger: #EF4444;
            --project-info: #06B6D4;

            /* Dégradés */
            --primary-gradient: linear-gradient(135deg, #3B82F6 0%, #1F2937 100%);
            --button-gradient: linear-gradient(90deg, #3B82F6 0%, #1F2937 100%);
            --button-gradient-hover: linear-gradient(90deg, #2563EB 0%, #111827 100%);
            --card-gradient: linear-gradient(135deg, #F5F8FF 0%, #FFFFFF 100%);
        }

        /* En-têtes de modules */
        .module-header {
            background: var(--primary-gradient);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 24px rgba(31, 41, 55, 0.25);
        }

        .module-header h1,
        .module-header h2,
        .module-header h3 {
            color: white !important;
            margin: 0;
        }

        /* Cartes */
        .info-card {
            background: var(--card-gradient);
            border: 1px solid var(--border-color-blue);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }

        /* Tableaux stylisés */
        .styled-table-header {
            display: grid;
            gap: 10px;
            background: var(--primary-gradient);
            color: white;
            padding: 12px;
            border-radius: 8px 8px 0 0;
            font-weight: 600;
            font-size: 0.9rem;
        }

        .styled-table-row {
            display: grid;
            gap: 10px;
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
            align-items: center;
            background: white;
            transition: background 0.2s;
        }

        .styled-table-row:hover {
            background: var(--background-color);
        }

        /* Badges de statut */
        .status-badge {
            display: inline-block;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.875rem;
        }

        .status-success {
            background: var(--project-success);
            color: white;
        }

        .status-warning {
            background: var(--project-warning);
            color: white;
        }

        .status-danger {
            background: var(--project-danger);
            color: white;
        }

        .status-info {
            background: var(--project-info);
            color: white;
        }

        .status-primary {
            background: var(--primary-color);
            color: white;
        }

        .status-muted {
            background: var(--text-color-muted);
            color: white;
        }

        /* Sections */
        .module-section {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-color);
        }

        .module-section h3 {
            color: var(--primary-color);
            margin-top: 0;
        }

        /* Alertes/Messages */
        .alert-info {
            background: var(--primary-color-lighter);
            border-left: 4px solid var(--primary-color);
            padding: 1rem;
            border-radius: 8px;
            color: var(--text-color);
        }

        .alert-success {
            background: #DCFCE7;
            border-left: 4px solid var(--project-success);
            padding: 1rem;
            border-radius: 8px;
            color: var(--text-color);
        }

        .alert-warning {
            background: #FEF3C7;
            border-left: 4px solid var(--project-warning);
            padding: 1rem;
            border-radius: 8px;
            color: var(--text-color);
        }

        /* Statistiques */
        .stat-card {
            background: var(--card-gradient);
            border: 1px solid var(--border-color-blue);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
            margin: 0.5rem 0;
        }

        .stat-label {
            color: var(--text-color-light);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
    </style>
    """
