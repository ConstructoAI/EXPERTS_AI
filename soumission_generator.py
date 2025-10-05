# soumission_generator.py
"""
Générateur de soumissions clients pour EXPERTS IA
Extrait les données d'estimation depuis les conversations et remplit template.html
"""

import json
import os
from datetime import datetime
from anthropic import Anthropic
from entreprise_config import get_entreprise_config, get_commercial_params


class SoumissionGenerator:
    """Gère l'extraction de données et la génération de soumissions clients."""

    def __init__(self, anthropic_client):
        """
        Initialise le générateur de soumissions.

        Args:
            anthropic_client: Instance de Anthropic API client
        """
        self.anthropic = anthropic_client
        self.model = "claude-sonnet-4-5-20250929"

    def extract_estimation_data(self, conversation_messages):
        """
        Utilise Claude pour extraire les données structurées d'estimation
        depuis l'historique de conversation.

        Args:
            conversation_messages: Liste des messages de la conversation

        Returns:
            dict: Données extraites structurées
        """

        # Charger les paramètres commerciaux de l'entreprise
        params_commerciaux = get_commercial_params()

        # Construire le contexte de conversation pour extraction
        conversation_text = self._format_conversation_for_extraction(conversation_messages)

        # Prompt spécialisé pour extraction
        extraction_prompt = f"""Tu es un expert en extraction de données pour soumissions de construction au Québec.

Analyse cette conversation entre un client et des experts en construction, puis extrais TOUTES les informations d'estimation en format JSON STRICT en étant ULTRA FIDÈLE à ce qui a été discuté.

CONVERSATION:
{conversation_text}

INSTRUCTIONS CRITIQUES - FIDÉLITÉ MAXIMALE À LA CONVERSATION:
1. **PRIORITÉ ABSOLUE**: Extrais UNIQUEMENT ce qui a été RÉELLEMENT mentionné dans la conversation
2. **NE PAS INVENTER**: Si une information n'a pas été discutée, utilise "À déterminer avec le client" ou laisse vide
3. **MONTANTS EXACTS**: Utilise les MONTANTS PRÉCIS donnés par l'expert (pas d'approximations)
4. **CITATIONS EXACTES**: Pour les détails, reprends les TERMES EXACTS utilisés par l'expert
5. **TOUS LES DÉTAILS**: Inclus CHAQUE spécification, dimension, matériau, norme mentionnée
6. **RATIOS ET CALCULS**: Extrais les ratios matériaux/main-d'œuvre TELS QUE MENTIONNÉS
7. **RECOMMANDATIONS**: Inclus toutes les recommandations et alternatives suggérées par l'expert
8. **CONTEXTE**: Inclus les contraintes, conditions du site, et notes importantes discutées
9. **QUANTITÉS**: Utilise les quantités EXACTES mentionnées (ne pas arrondir)
10. **SÉQUENCE**: Respecte l'ordre logique des travaux tel que discuté

STRUCTURE JSON REQUISE (RESPECTE EXACTEMENT CE FORMAT):

{{
    "numero_soumission": "2025-XXX",
    "date_soumission": "YYYY-MM-DD",

    "client": {{
        "nom": "",
        "adresse": "",
        "ville": "",
        "province": "Québec",
        "code_postal": ""
    }},

    "projet": {{
        "description": "",
        "type": "Construction neuve",
        "superficie_pi2": 0,
        "nb_etages": 1
    }},

    "contact": {{
        "nom": "",
        "telephone": "",
        "courriel": ""
    }},

    "travaux": [
        {{
            "categorie": "TRAVAUX PRÉPARATOIRES ET DÉMOLITION",
            "items": [
                {{
                    "description": "Permis et autorisations",
                    "details": "Permis de construction municipal, certificat de localisation, étude géotechnique si requise, études environnementales selon zonage, assurances chantier",
                    "quantite": 1,
                    "unite": "Forfait",
                    "materiaux": 0.00,
                    "materiaux_pct": 0,
                    "main_oeuvre": 0.00,
                    "main_oeuvre_pct": 100,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Préparation du terrain",
                    "details": "Déboisement, débroussaillage, démolition structures existantes si applicable, enlèvement débris, nivellement préliminaire",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "materiaux_pct": 20,
                    "main_oeuvre": 0.00,
                    "main_oeuvre_pct": 80,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "FONDATION ET STRUCTURE",
            "items": [
                {{
                    "description": "Excavation",
                    "details": "Excavation mécanique pour fondations selon plans, profondeur hors-gel (min 4 pi au Québec), transport et disposition surplus",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "materiaux_pct": 20,
                    "main_oeuvre": 0.00,
                    "main_oeuvre_pct": 80,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Semelles et murs de fondation",
                    "details": "Semelles béton armé #20M, murs fondation béton 8\" avec armature selon Code, drain français périmétrique, membrane imperméabilisation, isolation extérieure si requise",
                    "quantite": 0,
                    "unite": "pi lin.",
                    "materiaux": 0.00,
                    "materiaux_pct": 65,
                    "main_oeuvre": 0.00,
                    "main_oeuvre_pct": 35,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Dalle de béton",
                    "details": "Dalle 4\" sur pierre nette compactée, treillis métallique, membrane pare-vapeur 6 mil, isolation rigide selon CNB, finition lissée",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "materiaux_pct": 65,
                    "main_oeuvre": 0.00,
                    "main_oeuvre_pct": 35,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "CHARPENTE ET ENVELOPPE",
            "items": [
                {{
                    "description": "Charpente murale",
                    "details": "Ossature 2x6\" @ 16\" c/c, sablières traitées, linteaux selon portées, pare-air, contreventement selon CNB, plateforme d'étages",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Charpente de toit",
                    "details": "Fermes préfabriquées ou chevrons selon conception, pontage OSB 5/8\", supports ventilation, débords de toit",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Fenestration",
                    "details": "Portes et fenêtres certifiées Energy Star, installation selon normes d'étanchéité, solins intégrés",
                    "quantite": 0,
                    "unite": "unité",
                    "materiaux": 0.00,
                    "materiaux_pct": 75,
                    "main_oeuvre": 0.00,
                    "main_oeuvre_pct": 25,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "TOITURE",
            "items": [
                {{
                    "description": "Couverture de toiture",
                    "details": "Membrane d'étanchéité, bardeau d'asphalte architectural garantie 25-30 ans, sous-couche synthétique, solins galvanisés, ventilation soffit/faîte",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Système de drainage pluvial",
                    "details": "Gouttières aluminium calibre 0.027, descentes avec coudes, rallonges évacuation min 6 pi du bâtiment",
                    "quantite": 0,
                    "unite": "pi lin.",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "REVÊTEMENTS EXTÉRIEURS",
            "items": [
                {{
                    "description": "Revêtement mural",
                    "details": "Revêtement selon choix (vinyle/fibrociment/brique), pare-pluie/pare-air, fourrures si requis, joints de contrôle",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Finition et solins",
                    "details": "Solins métalliques, moulures décoratives, habillage soffit et fascia, caulking périmètre",
                    "quantite": 1,
                    "unite": "Forfait",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "PLOMBERIE",
            "items": [
                {{
                    "description": "Plomberie brute",
                    "details": "Tuyauterie PEX/cuivre, drains ABS selon code, évents de plomberie, robinets d'arrêt, préparation appareils sanitaires",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Appareils et finition",
                    "details": "Installation appareils sanitaires (toilettes, lavabos, douches), robinetterie, chauffe-eau électrique/gaz, raccordements finaux",
                    "quantite": 1,
                    "unite": "Forfait",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "ÉLECTRICITÉ",
            "items": [
                {{
                    "description": "Installation électrique",
                    "details": "Panneau 200A, filage cuivre NMD90, prises et interrupteurs, DDFT selon code, mise à la terre, luminaires inclus",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Systèmes spéciaux",
                    "details": "Câblage données/téléphone, détecteurs fumée/CO interconnectés, préparation domotique si demandé",
                    "quantite": 1,
                    "unite": "Forfait",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "CHAUFFAGE ET VENTILATION",
            "items": [
                {{
                    "description": "Système de chauffage",
                    "details": "Fournaise électrique/gaz, thermopompe ou système radiant selon choix, distribution air/eau, thermostats programmables",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Ventilation et échangeur d'air",
                    "details": "VRC/VRE selon CNB, conduits isolés, distribution équilibrée, filtration HEPA optionnelle",
                    "quantite": 1,
                    "unite": "Système",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "ISOLATION",
            "items": [
                {{
                    "description": "Isolation thermique",
                    "details": "Murs: laine R-24 minimum, plafond: soufflée R-50+, pare-vapeur polyéthylène 6 mil, scellant acoustique jonctions",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Étanchéité à l'air",
                    "details": "Test d'infiltrométrie, scellants aérosol, coupe-froid portes/fenêtres, certification Novoclimat optionnelle",
                    "quantite": 1,
                    "unite": "Forfait",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "FINITIONS INTÉRIEURES",
            "items": [
                {{
                    "description": "Revêtements muraux et plafonds",
                    "details": "Gypse 1/2\" type X coupe-feu, tirage joints niveau 4, peinture 2 couches latex, plafonds texturés ou lisses",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Revêtements de sol",
                    "details": "Plancher ingénierie/flottant, céramique salles d'eau, sous-plancher insonorisé, plinthes et moulures",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Portes et armoires",
                    "details": "Portes intérieures prépeintes, quincaillerie, armoires de cuisine et salle de bain selon choix, comptoirs",
                    "quantite": 1,
                    "unite": "Forfait",
                    "materiaux": 0.00,
                    "materiaux_pct": 80,
                    "main_oeuvre": 0.00,
                    "main_oeuvre_pct": 20,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }},
        {{
            "categorie": "AMÉNAGEMENT EXTÉRIEUR",
            "items": [
                {{
                    "description": "Aménagement paysager",
                    "details": "Nivellement final, ensemencement ou tourbe, plantation arbustes, paillis, bordures",
                    "quantite": 1,
                    "unite": "Forfait",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }},
                {{
                    "description": "Pavage et allées",
                    "details": "Entrée asphaltée ou pavée, trottoirs béton, drainage de surface, compactage granulaire",
                    "quantite": 0,
                    "unite": "pi²",
                    "materiaux": 0.00,
                    "main_oeuvre": 0.00,
                    "total": 0.00,
                    "prix_unitaire_global": 0.00
                }}
            ],
            "sous_total": 0.00,
            "sous_total_materiaux": 0.00,
            "sous_total_main_oeuvre": 0.00
        }}
    ],

    "recapitulatif": {{
        "total_travaux": 0.00,
        "administration_pct": {params_commerciaux['taux_administration']},
        "administration": 0.00,
        "contingences_pct": {params_commerciaux['taux_contingences']},
        "contingences": 0.00,
        "profit_pct": {params_commerciaux['taux_profit']},
        "profit": 0.00,
        "total_avant_taxes": 0.00,
        "tps_pct": 5.0,
        "tps": 0.00,
        "tvq_pct": 9.975,
        "tvq": 0.00,
        "investissement_total": 0.00
    }},

    "conditions": {{
        "validite_jours": 30,
        "delai_execution": "À déterminer",
        "notes_speciales": []
    }},

    "preparateur": {{
        "nom": "Expert IA",
        "titre": "Conseiller en estimation"
    }}
}}

CALCULS À EFFECTUER POUR CHAQUE ITEM:
1. Pour chaque item - EXTRAIS EN PRIORITÉ les ratios matériaux/main-d'œuvre de la CONVERSATION:

   ORDRE DE PRIORITÉ POUR DÉTERMINER LES RATIOS:

   A) PRIORITÉ 1 - CONVERSATION (si mentionné explicitement):
      - Si l'expert ou l'utilisateur a mentionné un ratio spécifique dans la conversation, UTILISE-LE
      - Exemples de ce qu'il faut chercher:
        * "60% matériaux et 40% main-d'œuvre"
        * "environ 70% de matériaux"
        * "la main-d'œuvre représente 55% du coût"
        * "ratio 65/35"
        * "principalement de la main-d'œuvre (80%)"
      - EXTRAIS les pourcentages exacts mentionnés par l'expert

   B) PRIORITÉ 2 - RATIOS STANDARDS (si NON mentionné dans conversation):
      Utilise ces ratios SEULEMENT si aucun ratio spécifique n'a été discuté:
      - Permis, études, gestion: 0% matériaux / 100% main-d'œuvre
      - Excavation, terrassement: 20% matériaux / 80% main-d'œuvre
      - Béton (fondations, dalles): 65% matériaux / 35% main-d'œuvre
      - Charpente bois: 60% matériaux / 40% main-d'œuvre
      - Toiture (bardeaux): 55% matériaux / 45% main-d'œuvre
      - Revêtements extérieurs: 50% matériaux / 50% main-d'œuvre
      - Fenestration: 75% matériaux / 25% main-d'œuvre
      - Plomberie (rough-in): 40% matériaux / 60% main-d'œuvre
      - Plomberie (finition): 70% matériaux / 30% main-d'œuvre
      - Électricité: 45% matériaux / 55% main-d'œuvre
      - CVAC (équipements): 70% matériaux / 30% main-d'œuvre
      - CVAC (installation): 40% matériaux / 60% main-d'œuvre
      - Isolation: 50% matériaux / 50% main-d'œuvre
      - Gypse et peinture: 35% matériaux / 65% main-d'œuvre
      - Planchers (matériaux): 75% matériaux / 25% main-d'œuvre
      - Armoires cuisine: 80% matériaux / 20% main-d'œuvre
      - Aménagement paysager: 40% matériaux / 60% main-d'œuvre

   Pour chaque item:
   - Cherche PRIORITAIREMENT si un ratio a été mentionné dans la conversation
   - Si OUI: utilise le ratio mentionné par l'expert
   - Si NON: utilise le ratio standard selon le type de travaux
   - materiaux_pct + main_oeuvre_pct = 100%
   - materiaux = total × (materiaux_pct / 100)
   - main_oeuvre = total × (main_oeuvre_pct / 100)
   - Vérifie: materiaux + main_oeuvre = total
   - prix_unitaire_global = total / superficie_totale_projet (si applicable)

2. Pour chaque catégorie:
   - sous_total = Somme de tous les "total" des items
   - sous_total_materiaux = Somme de tous les "materiaux" des items
   - sous_total_main_oeuvre = Somme de tous les "main_oeuvre" des items

3. Récapitulatif global:
   - total_travaux = Somme de tous les sous_totaux
   - administration = total_travaux × {params_commerciaux['taux_administration']}%
   - contingences = total_travaux × {params_commerciaux['taux_contingences']}%
   - profit = total_travaux × {params_commerciaux['taux_profit']}%
   - total_avant_taxes = total_travaux + administration + contingences + profit
   - tps = total_avant_taxes × 5%
   - tvq = total_avant_taxes × 9.975%
   - investissement_total = total_avant_taxes + tps + tvq

INSTRUCTIONS FINALES CRITIQUES:
1. Les exemples d'items ci-dessus sont des MODÈLES DÉTAILLÉS - adapte-les selon la conversation
2. REMPLACE les détails génériques par les spécifications EXACTES mentionnées dans la conversation
3. AJOUTE tous les détails techniques discutés (matériaux, dimensions, normes, options)
4. CONSERVE la structure détaillée même si non mentionné - utilise "selon choix" ou "à déterminer"
5. Pour chaque item, le champ "details" doit contenir au MINIMUM 2-3 phrases détaillées
6. Inclus les recommandations, alternatives et notes des experts dans les "details"

7. EXTRACTION DES MONTANTS ET RATIOS (ORDRE DE PRIORITÉ):
   a) Si l'expert a mentionné un montant TOTAL pour un item → utilise-le dans "total"
   b) Si l'expert a mentionné séparément "matériaux" et "main-d'œuvre" → utilise-les directement
   c) Si l'expert a mentionné un RATIO (ex: 60/40, 70% matériaux) → extrais-le dans materiaux_pct/main_oeuvre_pct
   d) Si RIEN n'est mentionné → utilise les ratios standards selon le type de travaux

8. Remplis OBLIGATOIREMENT les champs: materiaux_pct, main_oeuvre_pct (doivent totaliser 100%)
9. Remplis les champs "quantite" et "unite" selon les informations de la conversation
10. Calcule "prix_unitaire_global" = total / superficie_totale (si superficie mentionnée)
11. GARDE toutes les catégories, même si certaines ont sous_total = 0.00

IMPORTANT - VALIDATION JSON STRICTE:
1. Retourne UNIQUEMENT le JSON, sans texte avant ou après
2. Le JSON DOIT être strictement valide (pas de virgules en trop, guillemets doubles uniquement)
3. Vérifie que toutes les accolades et crochets sont bien fermés
4. Ne mets JAMAIS de virgule avant }} ou ]]
5. Utilise uniquement des guillemets doubles " (pas de guillemets simples ')
6. VÉRIFIE que chaque élément d'un tableau/objet (sauf le dernier) a une virgule à la fin
7. Après chaque objet/tableau, assure-toi qu'il y a une virgule SI ce n'est pas le dernier élément
8. Dans les valeurs string, échappe correctement les guillemets: \"
9. N'utilise PAS de sauts de ligne dans les valeurs string (utilise \\n)
10. Avant de retourner le JSON, relis-le mentalement pour vérifier la syntaxe

EXEMPLE DE STRUCTURE CORRECTE:
{{
    "items": [
        {{
            "nom": "Premier item",
            "valeur": 100
        }},
        {{
            "nom": "Deuxième item",
            "valeur": 200
        }}
    ],
    "autre_champ": "valeur"
}}

Note: Virgule APRÈS le premier objet, PAS de virgule après le deuxième (dernier).
"""

        try:
            print("[EXTRACTION] Appel API Claude pour extraction...")

            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=8000,  # Augmenté pour capturer plus de détails
                temperature=0.0,  # Température à 0 pour extraction fidèle et déterministe
                messages=[
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ]
            )

            if response.content and len(response.content) > 0:
                json_text = response.content[0].text.strip()

                # Nettoyer le JSON si nécessaire (enlever markdown)
                if json_text.startswith("```json"):
                    json_text = json_text.replace("```json", "").replace("```", "").strip()
                elif json_text.startswith("```"):
                    json_text = json_text.replace("```", "").strip()

                # Tentative de parsing JSON
                try:
                    data = json.loads(json_text)
                except json.JSONDecodeError as e:
                    # Tentative de réparation automatique
                    print(f"[EXTRACTION] ⚠️ Tentative de réparation du JSON...")
                    print(f"[EXTRACTION] Erreur: {str(e)}")

                    json_text_fixed = json_text

                    # Problème 1: virgule en trop avant } ou ]
                    json_text_fixed = json_text_fixed.replace(",}", "}").replace(",]", "]")

                    # Problème 2: virgule manquante entre éléments
                    # Détecter patterns comme: "value"\n    "key" et ajouter virgule
                    import re
                    json_text_fixed = re.sub(r'"\s*\n\s*"', '",\n    "', json_text_fixed)
                    json_text_fixed = re.sub(r'(\d+)\s*\n\s*"', r'\1,\n    "', json_text_fixed)
                    json_text_fixed = re.sub(r'}\s*\n\s*{', '},\n    {', json_text_fixed)
                    json_text_fixed = re.sub(r'}\s*\n\s*"', '},\n    "', json_text_fixed)
                    json_text_fixed = re.sub(r']\s*\n\s*"', '],\n    "', json_text_fixed)

                    # Problème 3: guillemets non échappés dans les valeurs
                    # (difficile à détecter automatiquement, on tente quand même)

                    try:
                        data = json.loads(json_text_fixed)
                        print(f"[EXTRACTION] ✅ JSON réparé avec succès!")
                    except json.JSONDecodeError as e2:
                        # Afficher le contexte de l'erreur pour debug
                        print(f"[EXTRACTION] ❌ Réparation échouée: {str(e2)}")
                        error_pos = getattr(e2, 'pos', 0)
                        start = max(0, error_pos - 150)
                        end = min(len(json_text_fixed), error_pos + 150)
                        print(f"[EXTRACTION] Contexte autour de l'erreur:")
                        print(f"...{json_text_fixed[start:end]}...")
                        # Relancer l'erreur originale
                        raise e

                # Ajouter numéro et date si manquants
                if not data.get("numero_soumission") or data["numero_soumission"] == "2025-XXX":
                    data["numero_soumission"] = self._generate_soumission_number()

                if not data.get("date_soumission"):
                    data["date_soumission"] = datetime.now().strftime("%Y-%m-%d")

                print(f"[EXTRACTION] ✅ Données extraites : {len(data.get('travaux', []))} catégories")
                return data
            else:
                raise Exception("Réponse vide de l'API Claude")

        except json.JSONDecodeError as e:
            print(f"[EXTRACTION] ❌ Erreur JSON: {str(e)}")
            print(f"[EXTRACTION] JSON problématique (premiers 500 caractères):")
            print(json_text[:500] if len(json_text) > 500 else json_text)
            print(f"[EXTRACTION] JSON problématique (autour de l'erreur):")
            # Afficher autour de la position de l'erreur
            error_pos = getattr(e, 'pos', 0)
            start = max(0, error_pos - 100)
            end = min(len(json_text), error_pos + 100)
            print(f"...{json_text[start:end]}...")
            raise Exception(f"Erreur de parsing JSON: {str(e)}\n\nLe JSON généré par l'IA contient une erreur de syntaxe. Veuillez réessayer.")
        except Exception as e:
            print(f"[EXTRACTION] ❌ Erreur: {str(e)}")
            raise Exception(f"Erreur lors de l'extraction: {str(e)}")

    def _format_conversation_for_extraction(self, messages):
        """Formate les messages pour l'extraction."""
        formatted = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                continue

            role_label = "Utilisateur" if role == "user" else "Expert"
            if role == "search_result":
                role_label = "Recherche Web"

            # Limiter longueur pour éviter dépassement contexte
            if isinstance(content, str) and len(content) > 2000:
                content = content[:2000] + "... [tronqué]"

            formatted.append(f"{role_label}: {content}")

        return "\n\n".join(formatted[-20:])  # Derniers 20 messages max

    def _generate_soumission_number(self):
        """
        Génère un numéro de soumission unique au format YYYY-NNN
        Exemple: 2025-001, 2025-002, etc.
        """
        from soumissions_db import get_all_soumissions, init_soumissions_table

        # Année actuelle
        annee_actuelle = datetime.now().year

        try:
            # Initialiser la table si nécessaire
            init_soumissions_table()

            # Compter les soumissions de cette année
            toutes_soumissions = get_all_soumissions(limit=1000)

            # Filtrer par année
            soumissions_annee = [
                s for s in toutes_soumissions
                if s.get('numero_soumission', '').startswith(str(annee_actuelle))
            ]

            # Prochain numéro séquentiel
            prochain_numero = len(soumissions_annee) + 1

            return f"{annee_actuelle}-{prochain_numero:03d}"

        except Exception as e:
            # En cas d'erreur, utiliser timestamp
            print(f"[WARN] Erreur génération numéro: {e}, utilisation timestamp")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            return f"{annee_actuelle}-{timestamp[-6:]}"

    def populate_template(self, data, template_path="template.html", client_from_db=None):
        """
        Remplit le template HTML avec les données extraites.

        Args:
            data: Dictionnaire de données extraites
            template_path: Chemin vers template.html
            client_from_db: Dictionnaire optionnel avec infos client de la BD (prioritaire)

        Returns:
            str: HTML final rempli
        """

        print(f"[TEMPLATE] Chargement de {template_path}...")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template introuvable: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # === REMPLACEMENTS SIMPLES ===

        # Charger la configuration d'entreprise
        config_entreprise = get_entreprise_config()
        params_commerciaux = get_commercial_params()

        # Remplacer les informations d'entreprise dans l'en-tête
        html = html.replace('Constructo AI Inc.', config_entreprise.get('nom', 'Constructo AI Inc.'))
        html = html.replace('1760 rue Jacques-Cartier Sud', config_entreprise.get('adresse', '1760 rue Jacques-Cartier Sud'))
        html = html.replace('Farnham (Québec) J2N 1Y8',
                          f"{config_entreprise.get('ville', 'Farnham')} ({config_entreprise.get('province', 'Québec')}) {config_entreprise.get('code_postal', 'J2N 1Y8')}")
        html = html.replace('Tél: 514-820-1972', f"Tél: {config_entreprise.get('telephone_bureau', '514-820-1972')}")
        html = html.replace('info@constructoai.ca | www.constructoai.ca',
                          f"{config_entreprise.get('email', 'info@constructoai.ca')} | {config_entreprise.get('site_web', 'www.constructoai.ca')}")
        html = html.replace('RBQ: 1234-5678-01 | NEQ: 1234567890',
                          f"RBQ: {config_entreprise.get('rbq', '1234-5678-01')} | NEQ: {config_entreprise.get('neq', '1234567890')}")
        html = html.replace('Excellence en construction intelligente', config_entreprise.get('slogan', 'Excellence en construction intelligente'))

        # En-tête de soumission - Numéro et Date
        date_actuelle = datetime.now().strftime('%Y-%m-%d')
        numero_soumission = data.get('numero_soumission', self._generate_soumission_number())

        html = html.replace('<?php echo date(\'Y-m-d\'); ?>', data.get('date_soumission', date_actuelle))
        html = html.replace('2025-001', numero_soumission)

        # S'assurer que les données contiennent le numéro et la date
        data['numero_soumission'] = numero_soumission
        data['date_soumission'] = data.get('date_soumission', date_actuelle)

        # Client - utiliser client_from_db en priorité si disponible
        if client_from_db:
            print("[TEMPLATE] Utilisation des données client de la BD")
            client = {
                'nom': client_from_db.get('nom', ''),
                'adresse': client_from_db.get('adresse', ''),
                'ville': client_from_db.get('ville', ''),
                'province': client_from_db.get('province', 'Québec'),
                'code_postal': client_from_db.get('code_postal', '')
            }
            # Utiliser le contact principal du client si disponible
            contact = {
                'nom': client_from_db.get('contact_principal_nom', ''),
                'telephone': client_from_db.get('contact_principal_telephone', ''),
                'courriel': client_from_db.get('contact_principal_email', '')
            }
        else:
            client = data.get('client', {})
            contact = data.get('contact', {})

        html = html.replace('[Nom du client]', client.get('nom', '[Nom du client]'))
        html = html.replace('[Adresse complète]', client.get('adresse', '[Adresse complète]'))
        html = html.replace('[Ville, Province]', f"{client.get('ville', '[Ville]')}, {client.get('province', 'Québec')}")
        html = html.replace('[H0H 0H0]', client.get('code_postal', '[H0H 0H0]'))

        # Projet
        projet = data.get('projet', {})
        html = html.replace('[Description du projet]', projet.get('description', '[Description du projet]'))
        html = html.replace('Construction neuve', projet.get('type', 'Construction neuve'))
        html = html.replace('[X] pi²', f"{projet.get('superficie_pi2', 0):,} pi²".replace(',', ' '))
        html = html.replace('<p><strong>Étages:</strong> [X]</p>', f"<p><strong>Étages:</strong> {projet.get('nb_etages', 1)}</p>")

        # Contact (déjà défini plus haut selon client_from_db ou data)
        html = html.replace('[Nom du contact]', contact.get('nom', '[Nom du contact]'))
        html = html.replace('[514-000-0000]', contact.get('telephone', '[514-000-0000]'))
        html = html.replace('[email@exemple.com]', contact.get('courriel', '[email@exemple.com]'))

        # === GÉNÉRATION TABLEAUX TRAVAUX ===

        travaux_html = self._generate_travaux_html(data.get('travaux', []))

        # Remplacer la section TRAVAUX PRÉPARATOIRES (exemple) par toutes les catégories
        # On cherche le pattern de section existant et on le remplace
        import re

        # Pattern pour trouver toutes les sections de travaux
        section_pattern = r'<div class="section">.*?</div>\s*</div>\s*(?=<!--|\s*<div class="summary-box">)'

        # Remplacer par nos sections générées
        html = re.sub(section_pattern, travaux_html, html, flags=re.DOTALL)

        # === GÉNÉRATION SOMMAIRE DES TRAVAUX ===

        sommaire_html = self._generate_sommaire_html(data.get('travaux', []))

        # Insérer le sommaire juste avant la section summary-box
        summary_pattern = r'(<div class="summary-box">)'
        html = re.sub(summary_pattern, sommaire_html + r'\1', html, count=1)

        # === RÉCAPITULATIF ===

        recap = data.get('recapitulatif', {})

        html = html.replace('>0,00 $</td>', f">{self._format_currency(recap.get('total_travaux', 0))}</td>", 1)

        # Remplacer chaque ligne du récapitulatif
        admin_pct = recap.get('administration_pct', params_commerciaux['taux_administration'])
        cont_pct = recap.get('contingences_pct', params_commerciaux['taux_contingences'])
        profit_pct = recap.get('profit_pct', params_commerciaux['taux_profit'])

        recap_replacements = [
            ('Travaux préparatoires:', recap.get('total_travaux', 0)),
            ('TOTAL DES TRAVAUX:', recap.get('total_travaux', 0)),
            ('Administration (3%):', recap.get('administration', 0)),
            ('Contingences (12%):', recap.get('contingences', 0)),
            ("Profit de l'entrepreneur (15%):", recap.get('profit', 0)),
            ('Total avant taxes:', recap.get('total_avant_taxes', 0)),
            ('TPS (5%):', recap.get('tps', 0)),
            ('TVQ (9.975%):', recap.get('tvq', 0)),
            ('INVESTISSEMENT TOTAL:', recap.get('investissement_total', 0))
        ]

        # Remplacer aussi les labels avec les bons pourcentages
        html = html.replace('Administration (3%)', f'Administration ({admin_pct}%)')
        html = html.replace('Contingences (12%)', f'Contingences ({cont_pct}%)')
        html = html.replace("Profit de l'entrepreneur (15%)", f"Profit de l'entrepreneur ({profit_pct}%)")

        for label, value in recap_replacements:
            pattern = f'<td class="label">(.*?){re.escape(label)}(.*?)</td>\\s*<td class="value">0,00 \\$</td>'
            replacement = f'<td class="label">\\1{label}\\2</td>\n                    <td class="value">{self._format_currency(value)}</td>'
            html = re.sub(pattern, replacement, html, count=1)

        # === CONDITIONS ===

        conditions = data.get('conditions', {})
        delai = conditions.get('delai_execution', 'À déterminer')
        html = html.replace('[X] semaines', delai)

        # === PRÉPARATEUR ===

        preparateur = data.get('preparateur', {})
        html = html.replace('[Nom], [Titre]', f"{preparateur.get('nom', 'Expert IA')}, {preparateur.get('titre', 'Conseiller')}")
        html = html.replace('[Nom]', preparateur.get('nom', 'Expert IA'))
        html = html.replace('[Titre]', preparateur.get('titre', 'Conseiller en estimation'))

        print("[TEMPLATE] ✅ Template rempli avec succès")

        return html

    def _generate_travaux_html(self, travaux_list):
        """Génère le HTML pour toutes les sections de travaux avec colonnes détaillées."""

        sections_html = []

        for categorie in travaux_list:
            cat_name = categorie.get('categorie', 'CATÉGORIE')
            items = categorie.get('items', [])
            sous_total = categorie.get('sous_total', 0)
            sous_total_mat = categorie.get('sous_total_materiaux', 0)
            sous_total_mo = categorie.get('sous_total_main_oeuvre', 0)

            # Ne générer que si la catégorie a des items
            if not items or len(items) == 0:
                continue

            # Début de section avec en-têtes de colonnes détaillées
            section_html = f'''
        <div class="section">
            <div class="section-title">{cat_name}</div>
            <table class="table">
                <thead>
                    <tr>
                        <th style="width: 30%;">Corps de métier</th>
                        <th style="width: 8%; text-align: center;">Quantité</th>
                        <th style="width: 8%; text-align: center;">Unité</th>
                        <th style="width: 13%; text-align: right;">Matériaux</th>
                        <th style="width: 13%; text-align: right;">Main-d'œuvre</th>
                        <th style="width: 13%; text-align: right;">Total</th>
                        <th style="width: 13%; text-align: right;">$/pi² global</th>
                    </tr>
                </thead>
                <tbody>
'''

            # Items
            for item in items:
                desc = item.get('description', '')
                details = item.get('details', '')
                qte = item.get('quantite', 0)
                unite = item.get('unite', 'pi²')
                materiaux = item.get('materiaux', 0)
                materiaux_pct = item.get('materiaux_pct', 60)
                main_oeuvre = item.get('main_oeuvre', 0)
                main_oeuvre_pct = item.get('main_oeuvre_pct', 40)
                total = item.get('total', 0)
                prix_unitaire = item.get('prix_unitaire_global', 0)

                section_html += f'''                    <tr>
                        <td>
                            <div class="item-description editable">{desc}</div>
                            <div class="item-details editable">{details}</div>
                        </td>
                        <td style="text-align: center;"><span class="editable">{qte if qte > 0 else '-'}</span></td>
                        <td style="text-align: center;"><span class="editable">{unite}</span></td>
                        <td style="text-align: right;">
                            <div style="font-weight: bold;" class="editable">{self._format_currency(materiaux)}</div>
                            <div style="font-size: 8px; color: #6b7280;"><span class="editable">({materiaux_pct}%)</span></div>
                        </td>
                        <td style="text-align: right;">
                            <div style="font-weight: bold;" class="editable">{self._format_currency(main_oeuvre)}</div>
                            <div style="font-size: 8px; color: #6b7280;"><span class="editable">({main_oeuvre_pct}%)</span></div>
                        </td>
                        <td style="text-align: right; font-weight: bold; color: #1f2937;"><span class="editable">{self._format_currency(total)}</span></td>
                        <td style="text-align: right; font-weight: bold; color: #6b7280;"><span class="editable">{self._format_currency(prix_unitaire)}</span></td>
                    </tr>
'''

            # Ligne de sous-total avec ventilation
            # Calculer les pourcentages globaux de la catégorie
            pct_mat_global = round((sous_total_mat / sous_total * 100), 0) if sous_total > 0 else 0
            pct_mo_global = round((sous_total_mo / sous_total * 100), 0) if sous_total > 0 else 0

            section_html += f'''                    <tr class="subtotal-row">
                        <td colspan="3" style="text-align: right; font-weight: bold;">Sous-total {cat_name}</td>
                        <td style="text-align: right;">
                            <div style="font-weight: bold;" class="editable">{self._format_currency(sous_total_mat)}</div>
                            <div style="font-size: 8px; color: #374151;"><span class="editable">({int(pct_mat_global)}%)</span></div>
                        </td>
                        <td style="text-align: right;">
                            <div style="font-weight: bold;" class="editable">{self._format_currency(sous_total_mo)}</div>
                            <div style="font-size: 8px; color: #374151;"><span class="editable">({int(pct_mo_global)}%)</span></div>
                        </td>
                        <td style="text-align: right; font-weight: bold; font-size: 11px;"><span class="editable">{self._format_currency(sous_total)}</span></td>
                        <td></td>
                    </tr>
                </tbody>
            </table>
        </div>
'''

            sections_html.append(section_html)

        return ''.join(sections_html)

    def _generate_sommaire_html(self, travaux_list):
        """Génère le HTML pour le sommaire des travaux (vue d'ensemble avant récapitulatif)."""

        # Filtrer seulement les catégories avec items
        categories_avec_travaux = [cat for cat in travaux_list if cat.get('items') and len(cat.get('items', [])) > 0]

        if not categories_avec_travaux:
            return ""

        sommaire_html = '''
        <!-- SOMMAIRE DES TRAVAUX -->
        <div style="margin-top: 30px; margin-bottom: 20px; padding: 20px; background: #f9fafb; border-radius: 6px; border-left: 4px solid #3b82f6;">
            <h4 style="margin-bottom: 15px; font-size: 13px; color: #374151; font-weight: 600;">SOMMAIRE DES TRAVAUX</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #e5e7eb; border-bottom: 2px solid #9ca3af;">
                        <th style="padding: 8px; text-align: left; font-weight: bold; font-size: 10px; color: #374151; width: 70%;">Catégorie</th>
                        <th style="padding: 8px; text-align: center; font-weight: bold; font-size: 10px; color: #374151; width: 15%;">Items</th>
                        <th style="padding: 8px; text-align: right; font-weight: bold; font-size: 10px; color: #374151; width: 15%;">Sous-total</th>
                    </tr>
                </thead>
                <tbody>
'''

        # Ajouter chaque catégorie
        for categorie in categories_avec_travaux:
            cat_name = categorie.get('categorie', 'CATÉGORIE')
            nb_items = len(categorie.get('items', []))
            sous_total = categorie.get('sous_total', 0)

            sommaire_html += f'''                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 8px; font-size: 10px; color: #374151;" class="editable">{cat_name}</td>
                        <td style="padding: 8px; text-align: center; font-size: 10px; color: #6b7280;" class="editable">{nb_items}</td>
                        <td style="padding: 8px; text-align: right; font-size: 10px; font-weight: bold; color: #111827; font-family: 'Courier New', monospace;" class="editable">{self._format_currency(sous_total)}</td>
                    </tr>
'''

        # Calculer le total
        total_travaux = sum(cat.get('sous_total', 0) for cat in categories_avec_travaux)

        sommaire_html += f'''                    <tr style="background: #dbeafe; border-top: 2px solid #3b82f6; font-weight: bold;">
                        <td style="padding: 10px; font-size: 11px; color: #1e40af;">TOTAL DES TRAVAUX</td>
                        <td style="padding: 10px; text-align: center; font-size: 10px; color: #1e40af;" class="editable">{sum(len(cat.get('items', [])) for cat in categories_avec_travaux)} items</td>
                        <td style="padding: 10px; text-align: right; font-size: 12px; font-weight: bold; color: #1e3a8a; font-family: 'Courier New', monospace;" class="editable">{self._format_currency(total_travaux)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
'''

        return sommaire_html

    def _format_currency(self, value):
        """Formate un nombre en devise canadienne."""
        try:
            amount = float(value)
            # Format avec espace comme séparateur de milliers (standard québécois)
            formatted = f"{amount:,.2f} $".replace(',', ' ')
            return formatted
        except (ValueError, TypeError):
            return "0,00 $"
