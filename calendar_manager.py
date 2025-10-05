"""
Gestionnaire de calendrier central pour EXPERTS IA
Connecte tous les modules avec un système de calendrier unifié
"""

import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta, date
import calendar as cal
import pandas as pd

# Définir le répertoire de données
DATA_DIR = os.getenv('DATA_DIR', 'data')
DB_PATH = os.path.join(DATA_DIR, 'calendrier.db')


def init_calendar_db():
    """Initialise la base de données du calendrier"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except PermissionError:
        pass  # Utiliser le répertoire courant si permission refusée

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calendrier_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            description TEXT,
            date_debut TEXT NOT NULL,
            date_fin TEXT,
            type_event TEXT NOT NULL,
            reference_id TEXT,
            client_nom TEXT,
            statut TEXT DEFAULT 'en_attente',
            couleur TEXT DEFAULT '#4b5563',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def add_event(titre, description, date_debut, date_fin=None, type_event="autre",
              reference_id=None, client_nom=None, statut="en_attente", couleur="#4b5563"):
    """Ajoute un événement au calendrier"""
    init_calendar_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Convertir les dates en string si nécessaire
    if isinstance(date_debut, (date, datetime)):
        date_debut = date_debut.strftime('%Y-%m-%d %H:%M:%S')
    if date_fin and isinstance(date_fin, (date, datetime)):
        date_fin = date_fin.strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
        INSERT INTO calendrier_events
        (titre, description, date_debut, date_fin, type_event, reference_id, client_nom, statut, couleur)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (titre, description, date_debut, date_fin, type_event, reference_id, client_nom, statut, couleur))

    event_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return event_id


def get_all_events():
    """Récupère tous les événements"""
    init_calendar_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, titre, description, date_debut, date_fin, type_event,
               reference_id, client_nom, statut, couleur, created_at
        FROM calendrier_events
        ORDER BY date_debut DESC
    """)

    columns = ['id', 'titre', 'description', 'date_debut', 'date_fin', 'type_event',
               'reference_id', 'client_nom', 'statut', 'couleur', 'created_at']

    events = []
    for row in cursor.fetchall():
        events.append(dict(zip(columns, row)))

    conn.close()
    return events


def get_events_by_month(year, month):
    """Récupère les événements d'un mois donné"""
    init_calendar_db()

    # Dates de début et fin du mois
    first_day = f"{year}-{month:02d}-01"
    if month == 12:
        last_day = f"{year + 1}-01-01"
    else:
        last_day = f"{year}-{month + 1:02d}-01"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, titre, description, date_debut, date_fin, type_event,
               reference_id, client_nom, statut, couleur
        FROM calendrier_events
        WHERE date_debut >= ? AND date_debut < ?
        ORDER BY date_debut
    """, (first_day, last_day))

    columns = ['id', 'titre', 'description', 'date_debut', 'date_fin', 'type_event',
               'reference_id', 'client_nom', 'statut', 'couleur']

    events = []
    for row in cursor.fetchall():
        events.append(dict(zip(columns, row)))

    conn.close()
    return events


def get_upcoming_events(days=7):
    """Récupère les événements à venir dans les X prochains jours"""
    init_calendar_db()

    today = datetime.now().strftime('%Y-%m-%d')
    future_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, titre, description, date_debut, date_fin, type_event,
               reference_id, client_nom, statut, couleur
        FROM calendrier_events
        WHERE date_debut >= ? AND date_debut <= ?
        ORDER BY date_debut
        LIMIT 10
    """, (today, future_date))

    columns = ['id', 'titre', 'description', 'date_debut', 'date_fin', 'type_event',
               'reference_id', 'client_nom', 'statut', 'couleur']

    events = []
    for row in cursor.fetchall():
        events.append(dict(zip(columns, row)))

    conn.close()
    return events


def update_event(event_id, **kwargs):
    """Met à jour un événement"""
    init_calendar_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Construire la requête dynamiquement
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in ['titre', 'description', 'date_debut', 'date_fin', 'type_event',
                   'reference_id', 'client_nom', 'statut', 'couleur']:
            fields.append(f"{key} = ?")
            values.append(value)

    if fields:
        query = f"UPDATE calendrier_events SET {', '.join(fields)} WHERE id = ?"
        values.append(event_id)
        cursor.execute(query, values)
        conn.commit()

    conn.close()


def delete_event(event_id):
    """Supprime un événement"""
    init_calendar_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM calendrier_events WHERE id = ?", (event_id,))

    conn.commit()
    conn.close()


def get_event_colors():
    """Retourne les couleurs par type d'événement"""
    return {
        'soumission': '#3B82F6',      # Bleu
        'bon_commande': '#10b981',     # Vert
        'client': '#f59e0b',           # Orange
        'reunion': '#8b5cf6',          # Violet
        'livraison': '#06b6d4',        # Cyan
        'echeance': '#ef4444',         # Rouge
        'suivi': '#6366f1',            # Indigo
        'autre': '#6b7280'             # Gris
    }


def show_calendar_interface():
    """Interface principale du calendrier"""
    st.markdown("## 📅 Calendrier des Événements")
    st.markdown("Gérez tous vos événements, échéances et rendez-vous en un seul endroit.")

    # Initialiser la DB
    init_calendar_db()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Vue Calendrier", "📋 Liste", "➕ Ajouter", "📊 Statistiques"])

    with tab1:
        show_calendar_view()

    with tab2:
        show_events_list()

    with tab3:
        show_add_event_form()

    with tab4:
        show_calendar_stats()


def show_calendar_view():
    """Affiche la vue calendrier mensuelle"""
    st.markdown("### 📅 Vue Mensuelle")

    # Sélection du mois
    col1, col2, col3 = st.columns([2, 3, 2])

    with col1:
        current_year = datetime.now().year
        year = st.selectbox("Année", range(current_year - 2, current_year + 3),
                           index=2, key="cal_year")

    with col2:
        months = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        current_month = datetime.now().month
        month = st.selectbox("Mois", range(1, 13),
                            format_func=lambda x: months[x-1],
                            index=current_month - 1, key="cal_month")

    # Récupérer les événements du mois
    events = get_events_by_month(year, month)

    # Créer un dictionnaire des événements par jour
    events_by_day = {}
    for event in events:
        try:
            event_date = datetime.strptime(event['date_debut'][:10], '%Y-%m-%d')
            day = event_date.day
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)
        except:
            pass

    # Afficher le calendrier
    cal_obj = cal.Calendar(firstweekday=6)  # Dimanche = 0
    month_days = cal_obj.monthdayscalendar(year, month)

    # En-tête des jours
    st.markdown("""
        <style>
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
            margin-top: 20px;
        }
        .calendar-day-header {
            background: #4b5563;
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            border-radius: 5px;
        }
        .calendar-day {
            background: #FAFBFF;
            border: 1px solid #E5E7EB;
            border-radius: 5px;
            padding: 10px;
            min-height: 100px;
            position: relative;
        }
        .calendar-day-number {
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        .calendar-day-today {
            background: #dbeafe;
            border: 2px solid #3B82F6;
        }
        .calendar-event {
            background: #3B82F6;
            color: white;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 0.75em;
            margin: 2px 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        </style>
    """, unsafe_allow_html=True)

    days_header = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam']

    calendar_html = '<div class="calendar-grid">'

    # En-têtes
    for day_name in days_header:
        calendar_html += f'<div class="calendar-day-header">{day_name}</div>'

    # Jours du mois
    today = datetime.now()
    for week in month_days:
        for day in week:
            if day == 0:
                calendar_html += '<div class="calendar-day" style="background: #E5E7EB;"></div>'
            else:
                is_today = (day == today.day and month == today.month and year == today.year)
                day_class = "calendar-day-today" if is_today else ""

                calendar_html += f'<div class="calendar-day {day_class}">'
                calendar_html += f'<div class="calendar-day-number">{day}</div>'

                # Ajouter les événements du jour
                if day in events_by_day:
                    for event in events_by_day[day][:3]:  # Max 3 événements affichés
                        event_color = event.get('couleur', '#4b5563')
                        calendar_html += f'<div class="calendar-event" style="background: {event_color};">{event["titre"][:20]}</div>'

                    if len(events_by_day[day]) > 3:
                        calendar_html += f'<div style="font-size: 0.7em; color: #6b7280; margin-top: 2px;">+{len(events_by_day[day]) - 3} autre(s)</div>'

                calendar_html += '</div>'

    calendar_html += '</div>'

    st.markdown(calendar_html, unsafe_allow_html=True)

    # Légende
    st.markdown("---")
    st.markdown("### 🎨 Légende des couleurs")
    colors = get_event_colors()
    cols = st.columns(4)
    for idx, (type_name, color) in enumerate(colors.items()):
        with cols[idx % 4]:
            st.markdown(f'<span style="background: {color}; color: white; padding: 3px 10px; border-radius: 3px; display: inline-block; margin: 2px;">{type_name.replace("_", " ").title()}</span>', unsafe_allow_html=True)


def show_events_list():
    """Affiche la liste des événements"""
    st.markdown("### 📋 Liste des Événements")

    # Filtres
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_type = st.selectbox("Type", ["Tous", "soumission", "bon_commande", "client",
                                            "reunion", "livraison", "echeance", "suivi", "autre"],
                                   key="filter_type")

    with col2:
        filter_statut = st.selectbox("Statut", ["Tous", "en_attente", "confirme", "termine", "annule"],
                                     key="filter_statut")

    with col3:
        sort_by = st.selectbox("Trier par", ["Date (récent)", "Date (ancien)", "Titre"],
                              key="sort_by")

    # Récupérer les événements
    events = get_all_events()

    # Appliquer les filtres
    if filter_type != "Tous":
        events = [e for e in events if e['type_event'] == filter_type]

    if filter_statut != "Tous":
        events = [e for e in events if e['statut'] == filter_statut]

    # Trier
    if sort_by == "Date (ancien)":
        events = sorted(events, key=lambda x: x['date_debut'])
    elif sort_by == "Titre":
        events = sorted(events, key=lambda x: x['titre'])

    # Afficher les événements
    if not events:
        st.info("Aucun événement trouvé.")
    else:
        st.markdown(f"**{len(events)} événement(s) trouvé(s)**")

        for event in events:
            with st.expander(f"📅 {event['titre']} - {event['date_debut'][:10]}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Type:** {event['type_event'].replace('_', ' ').title()}")
                    st.markdown(f"**Statut:** {event['statut'].replace('_', ' ').title()}")
                    if event['client_nom']:
                        st.markdown(f"**Client:** {event['client_nom']}")
                    if event['description']:
                        st.markdown(f"**Description:** {event['description']}")
                    if event['reference_id']:
                        st.markdown(f"**Référence:** {event['reference_id']}")
                    st.markdown(f"**Date:** {event['date_debut']}")
                    if event['date_fin']:
                        st.markdown(f"**Date fin:** {event['date_fin']}")

                with col2:
                    if st.button("🗑️ Supprimer", key=f"del_{event['id']}"):
                        delete_event(event['id'])
                        st.success("Événement supprimé!")
                        st.rerun()


def show_add_event_form():
    """Formulaire d'ajout d'événement"""
    st.markdown("### ➕ Ajouter un Événement")

    with st.form("add_event_form"):
        titre = st.text_input("Titre *", placeholder="Ex: Rendez-vous client, Livraison matériaux...")

        col1, col2 = st.columns(2)
        with col1:
            date_debut = st.date_input("Date de début *", value=datetime.now())
            heure_debut = st.time_input("Heure de début", value=datetime.now().time())

        with col2:
            date_fin = st.date_input("Date de fin (optionnel)")
            heure_fin = st.time_input("Heure de fin (optionnel)")

        col3, col4 = st.columns(2)
        with col3:
            type_event = st.selectbox("Type *",
                                     ["soumission", "bon_commande", "client", "reunion",
                                      "livraison", "echeance", "suivi", "autre"])

        with col4:
            statut = st.selectbox("Statut *",
                                 ["en_attente", "confirme", "termine", "annule"])

        col5, col6 = st.columns(2)
        with col5:
            client_nom = st.text_input("Nom du client (optionnel)")

        with col6:
            reference_id = st.text_input("Référence (optionnel)",
                                        placeholder="Ex: Soumission #123")

        description = st.text_area("Description (optionnel)")

        # Couleur basée sur le type
        colors = get_event_colors()
        couleur = colors.get(type_event, '#6b7280')

        submitted = st.form_submit_button("➕ Ajouter l'événement", use_container_width=True)

        if submitted:
            if not titre:
                st.error("Le titre est obligatoire!")
            else:
                # Combiner date et heure
                datetime_debut = datetime.combine(date_debut, heure_debut)
                datetime_fin = None
                if date_fin:
                    datetime_fin = datetime.combine(date_fin, heure_fin) if heure_fin else datetime.combine(date_fin, datetime.now().time())

                event_id = add_event(
                    titre=titre,
                    description=description,
                    date_debut=datetime_debut,
                    date_fin=datetime_fin,
                    type_event=type_event,
                    reference_id=reference_id,
                    client_nom=client_nom,
                    statut=statut,
                    couleur=couleur
                )

                st.success(f"✅ Événement #{event_id} ajouté avec succès!")
                st.balloons()


def show_calendar_stats():
    """Affiche les statistiques du calendrier"""
    st.markdown("### 📊 Statistiques")

    events = get_all_events()

    if not events:
        st.info("Aucun événement enregistré.")
        return

    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Événements", len(events))

    with col2:
        upcoming = get_upcoming_events(7)
        st.metric("À venir (7 jours)", len(upcoming))

    with col3:
        en_attente = len([e for e in events if e['statut'] == 'en_attente'])
        st.metric("En attente", en_attente)

    with col4:
        termine = len([e for e in events if e['statut'] == 'termine'])
        st.metric("Terminés", termine)

    # Répartition par type
    st.markdown("---")
    st.markdown("#### Répartition par Type")

    type_counts = {}
    for event in events:
        type_name = event['type_event']
        type_counts[type_name] = type_counts.get(type_name, 0) + 1

    if type_counts:
        df_types = pd.DataFrame(list(type_counts.items()), columns=['Type', 'Nombre'])
        df_types = df_types.sort_values('Nombre', ascending=False)
        st.bar_chart(df_types.set_index('Type'))

    # Événements récents
    st.markdown("---")
    st.markdown("#### Événements Récents")

    for event in events[:5]:
        st.markdown(f"- **{event['titre']}** ({event['type_event']}) - {event['date_debut'][:10]}")


def show_upcoming_events_widget():
    """Widget compact des événements à venir (pour sidebar)"""
    upcoming = get_upcoming_events(7)

    if upcoming:
        st.markdown("#### 📅 Événements à venir")
        for event in upcoming[:3]:
            date_str = event['date_debut'][:10]
            st.markdown(f"**{date_str}** - {event['titre']}")

        if len(upcoming) > 3:
            st.caption(f"+{len(upcoming) - 3} autre(s) événement(s)")


# Initialiser la base de données au chargement du module
init_calendar_db()
