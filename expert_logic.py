# expert_logic.py
# REMINDER: Update requirements.txt if needed

import os
import io
import base64
import csv
from datetime import datetime
import time # Import time for potential delays/retries

import PyPDF2
import docx
# import openpyxl # Uncomment this line ONLY if you keep/uncomment the XLSX reading code below
from PIL import Image
from anthropic import Anthropic, APIError # Importer APIError pour une meilleure gestion des erreurs

# Constants
SEPARATOR_DOUBLE = "=" * 50
SEPARATOR_SINGLE = "-" * 50

# --- ExpertProfileManager Class ---
class ExpertProfileManager:
    def __init__(self, profile_dir="profiles"):
        self.profiles = {}
        self.profile_dir = profile_dir
        self.load_profiles()

    def load_profiles(self):
        """Charge les profils experts depuis le dossier spécifié."""
        print(f"Chargement des profils depuis: {self.profile_dir}")
        if not os.path.exists(self.profile_dir):
            print(f"AVERTISSEMENT: Le dossier de profils '{self.profile_dir}' n'existe pas.")
            if not self.profiles:
                 self.add_profile("default_expert", "Expert par Défaut", "Je suis un expert IA généraliste.")
            return

        try:
            profile_files = [f for f in os.listdir(self.profile_dir) if f.endswith('.txt')]
            if not profile_files:
                 print("Aucun fichier de profil .txt trouvé.")
                 if not self.profiles:
                     self.add_profile("default_expert", "Expert par Défaut", "Je suis un expert IA généraliste.")
                 return

            for profile_file in profile_files:
                profile_id = os.path.splitext(profile_file)[0]
                profile_path = os.path.join(self.profile_dir, profile_file)
                try:
                    with open(profile_path, 'r', encoding='utf-8') as file:
                        content = file.read().strip()
                        if not content:
                            print(f"AVERTISSEMENT: Fichier de profil vide: {profile_file}")
                            continue
                        lines = content.split('\n', 1)
                        name = lines[0].strip() if lines else f"Profil_{profile_id}"
                        profile_content = lines[1].strip() if len(lines) > 1 else f"Profil: {name}"
                        self.add_profile(profile_id, name, profile_content)
                        print(f"Profil chargé: {profile_id} - {name}")
                except Exception as e:
                    print(f"Erreur lors du chargement du profil {profile_file}: {str(e)}")

        except Exception as e:
            print(f"Erreur lors de l'accès au dossier des profils '{self.profile_dir}': {str(e)}")
            if not self.profiles:
                 self.add_profile("default_expert", "Expert par Défaut", "Je suis un expert IA généraliste.")


    def add_profile(self, profile_id, display_name, profile_content):
        self.profiles[profile_id] = {
            "id": profile_id,
            "name": display_name,
            "content": profile_content
        }

    def get_profile(self, profile_id):
        return self.profiles.get(profile_id, None)

    def get_profile_by_name(self, name):
        for profile in self.profiles.values():
            if profile["name"] == name:
                return profile
        return None

    def get_all_profiles(self):
        return self.profiles

    def get_profile_names(self):
        if not self.profiles:
            self.load_profiles()
        names = [p["name"] for p in self.profiles.values()]
        # ✅ Tri alphabétique avec support des accents français
        import unicodedata
        def normalize_for_sort(text):
            """Normalise le texte pour le tri en supprimant les accents."""
            return unicodedata.normalize('NFD', text.lower()).encode('ascii', 'ignore').decode('ascii')
        
        return sorted(names, key=normalize_for_sort)


# --- ExpertAdvisor Class ---
class ExpertAdvisor:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Clé API Anthropic manquante.")
        self.anthropic = Anthropic(api_key=api_key)
        print("Client API Anthropic initialisé.")
        self.model_name_global = "claude-opus-4-1-20250805" # Votre modèle unique
        print(f"Utilisation globale du modèle : {self.model_name_global}")

        # Support étendu des formats - 27 types de fichiers
        self.supported_formats = [
            # Documents
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv', '.txt', '.rtf', '.md',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            # Code
            '.py', '.js', '.html', '.htm', '.css', '.json', '.xml', '.yaml', '.yml',
            # Audio
            '.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac'
        ]
        
        self.profile_manager = ExpertProfileManager()
        all_profiles = self.profile_manager.get_all_profiles()
        self.current_profile_id = list(all_profiles.keys())[0] if all_profiles else "default_expert"
        if not all_profiles:
             if not self.profile_manager.get_profile("default_expert"):
                 self.profile_manager.add_profile("default_expert", "Expert par Défaut", "Je suis un expert IA généraliste.")
             self.current_profile_id = "default_expert"

    def set_current_profile_by_name(self, profile_name):
        profile = self.profile_manager.get_profile_by_name(profile_name)
        if profile:
            self.current_profile_id = profile["id"]
            print(f"Profil expert changé en: {profile_name}")
            return True
        print(f"Erreur: Profil '{profile_name}' non trouvé.")
        return False

    def get_current_profile(self):
        profile = self.profile_manager.get_profile(self.current_profile_id)
        if not profile:
             available_profiles = self.profile_manager.get_all_profiles()
             if available_profiles:
                 first_profile_id = next(iter(available_profiles))
                 self.current_profile_id = first_profile_id
                 print(f"Avertissement: Profil ID {self.current_profile_id} invalide, retour au premier profil disponible: {first_profile_id}")
                 return available_profiles[first_profile_id]
             else:
                 print("Avertissement: Aucun profil chargé, utilisation d'un profil interne par défaut.")
                 return {"id": "default", "name": "Expert (Défaut)", "content": "Expert IA"}
        return profile

    def get_supported_filetypes_flat(self):
        return [ext.lstrip('.') for ext in self.supported_formats]

    def _validate_file_security(self, uploaded_file):
        """Valide la sécurité d'un fichier uploadé."""
        file_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name
        file_ext = os.path.splitext(filename)[1].lower()
        
        # 1. Vérification de la taille (limite 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_bytes) > max_size:
            return f"❌ Fichier trop volumineux: {filename}. Taille maximum: 50MB"
        
        # 2. Vérification des caractères dangereux dans le nom
        dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\x00']
        if any(char in filename for char in dangerous_chars):
            return f"❌ Nom de fichier non sécurisé: {filename}. Caractères interdits détectés."
        
        # 3. Vérification des signatures de fichiers (magic numbers)
        magic_signatures = {
            '.pdf': [b'%PDF'],
            '.png': [b'\x89PNG\r\n\x1a\n'],
            '.jpg': [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\xff\xd8\xff\xdb'],
            '.jpeg': [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\xff\xd8\xff\xdb'],
            '.gif': [b'GIF87a', b'GIF89a'],
            '.bmp': [b'BM'],
            '.webp': [b'RIFF'],
            '.docx': [b'PK\x03\x04'],  # ZIP format
            '.xlsx': [b'PK\x03\x04'],  # ZIP format
        }
        
        if file_ext in magic_signatures:
            file_start = file_bytes[:20]  # Premiers 20 bytes
            valid_signature = False
            for signature in magic_signatures[file_ext]:
                if file_start.startswith(signature):
                    valid_signature = True
                    break
            
            if not valid_signature:
                return f"❌ Signature de fichier invalide: {filename}. Le fichier pourrait être corrompu ou malveillant."
        
        # 4. Vérifications spécifiques pour les fichiers texte
        if file_ext in ['.txt', '.csv', '.json', '.xml', '.yaml', '.yml', '.py', '.js', '.html', '.htm', '.css']:
            try:
                # Vérifier l'encodage et détecter les contenus suspects
                text_content = file_bytes.decode('utf-8', errors='ignore')
                
                # Détecter des patterns suspects
                suspicious_patterns = [
                    'eval(', 'exec(', '<script', '<?php', '<%', 
                    'DROP TABLE', 'DELETE FROM', 'UPDATE SET',
                    'javascript:', 'vbscript:', 'data:',
                    '__import__', 'subprocess.', 'os.system'
                ]
                
                text_lower = text_content.lower()
                for pattern in suspicious_patterns:
                    if pattern.lower() in text_lower:
                        print(f"SÉCURITÉ: Pattern suspect détecté dans {filename}: {pattern}")
                        # Log mais ne bloque pas (pourrait être légitime dans un contexte de construction)
            except:
                pass  # Erreur de décodage, mais on continue
        
        return None  # Aucune erreur détectée

    def read_file(self, uploaded_file):
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in self.supported_formats:
            return f"Format de fichier non supporté: {uploaded_file.name}. Formats acceptés: {', '.join(self.supported_formats)}"
        
        # 🔒 VALIDATION DE SÉCURITÉ
        security_error = self._validate_file_security(uploaded_file)
        if security_error:
            return security_error
        
        try:
            file_bytes = uploaded_file.getvalue()
            file_stream = io.BytesIO(file_bytes)
            print(f"🔒 SÉCURITÉ: Fichier validé - {uploaded_file.name} ({len(file_bytes)} bytes)")
            
            # Documents PDF
            if file_ext == '.pdf':
                return self._read_pdf(file_stream, uploaded_file.name)
            
            # Documents Word
            elif file_ext == '.docx':
                return self._read_docx(file_stream, uploaded_file.name)
            elif file_ext == '.doc':
                return self._read_doc_legacy(file_bytes, uploaded_file.name)
            
            # Tableurs et CSV
            elif file_ext in ['.xlsx', '.xls', '.csv']:
                return self._read_spreadsheet(file_stream, uploaded_file.name, file_ext)
            
            # Texte et documents légers
            elif file_ext in ['.txt', '.md', '.rtf']:
                return self._read_text_document(file_stream, uploaded_file.name, file_ext)
            
            # Images
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                return self._read_image(file_bytes, uploaded_file.name, file_ext)
            
            # Code
            elif file_ext in ['.py', '.js', '.html', '.htm', '.css', '.json', '.xml', '.yaml', '.yml']:
                return self._read_code_file(file_stream, uploaded_file.name, file_ext)
            
            # Audio
            elif file_ext in ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']:
                return self._read_audio_file(file_bytes, uploaded_file.name, file_ext)
            
            else:
                return f"Format de fichier interne non géré : {uploaded_file.name}"
                
        except Exception as e:
            return f"Erreur générale lors de la lecture du fichier {uploaded_file.name}: {str(e)}"

    def _read_pdf(self, file_stream, filename):
        text = ""
        try:
            file_stream.seek(0)
            pdf_reader = PyPDF2.PdfReader(file_stream)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text: text += page_text + "\n"
            if not text: return f"Aucun texte n'a pu être extrait de {filename}. Le PDF est-il basé sur une image ou protégé ?"
            return text
        except Exception as e: return f"Erreur lors de la lecture du PDF {filename}: {str(e)}"

    def _read_docx(self, file_stream, filename):
        try:
            file_stream.seek(0)
            doc = docx.Document(file_stream)
            return "\n".join([p.text for p in doc.paragraphs if p.text is not None])
        except Exception as e: return f"Erreur lors de la lecture du DOCX {filename}: {str(e)}"

    def _read_doc_legacy(self, file_bytes, filename):
        try:
            # Tentative avec docx2txt si disponible
            try:
                import docx2txt
                text = docx2txt.process(io.BytesIO(file_bytes))
                return text if text else f"Aucun contenu texte extrait de {filename}"
            except ImportError:
                return f"INFO: Lecture des fichiers .DOC nécessite la bibliothèque 'docx2txt'. Veuillez l'installer : pip install docx2txt"
        except Exception as e:
            return f"Erreur lors de la lecture du DOC {filename}: {str(e)}"

    def _read_spreadsheet(self, file_stream, filename, file_ext):
        try:
            if file_ext == '.csv':
                file_stream.seek(0)
                decoded_content = None
                try: decoded_content = file_stream.read().decode('utf-8')
                except UnicodeDecodeError:
                    print(f"Décodage UTF-8 échoué pour {filename}, essai avec Latin-1.")
                    file_stream.seek(0)
                    try: decoded_content = file_stream.read().decode('latin1')
                    except Exception as de: return f"Erreur de décodage pour {filename}: {str(de)}"
                if decoded_content is None: return f"Impossible de décoder le contenu de {filename}."
                text_stream = io.StringIO(decoded_content)
                reader = csv.reader(text_stream)
                output_string_io = io.StringIO()
                writer = csv.writer(output_string_io, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                for row in reader: writer.writerow(row)
                return output_string_io.getvalue()
            
            elif file_ext == '.xlsx':
                try:
                    import openpyxl
                    file_stream.seek(0)
                    workbook = openpyxl.load_workbook(file_stream)
                    sheet = workbook.active
                    csv_output = io.StringIO()
                    writer = csv.writer(csv_output)
                    for row in sheet.iter_rows(values_only=True):
                        writer.writerow([str(cell) if cell is not None else "" for cell in row])
                    return csv_output.getvalue()
                except ImportError:
                    return "INFO: La bibliothèque 'openpyxl' est requise pour lire les fichiers .xlsx. Veuillez l'installer."
                except Exception as e_xlsx:
                    return f"Erreur lors de la lecture du XLSX {filename}: {str(e_xlsx)}"
            
            elif file_ext == '.xls':
                try:
                    import xlrd
                    file_stream.seek(0)
                    workbook = xlrd.open_workbook(file_contents=file_stream.read())
                    sheet = workbook.sheet_by_index(0)
                    csv_output = io.StringIO()
                    writer = csv.writer(csv_output)
                    for row_idx in range(sheet.nrows):
                        row = [str(cell.value) for cell in sheet.row(row_idx)]
                        writer.writerow(row)
                    return csv_output.getvalue()
                except ImportError:
                    return "INFO: La bibliothèque 'xlrd' est requise pour lire les fichiers .xls. Veuillez l'installer."
                except Exception as e_xls:
                    return f"Erreur lors de la lecture du XLS {filename}: {str(e_xls)}"
                    
        except Exception as e: 
            return f"Erreur lors du traitement du tableur {filename}: {str(e)}"

    def _read_text_document(self, file_stream, filename, file_ext):
        try:
            file_stream.seek(0)
            raw_bytes = file_stream.read()
            
            if file_ext == '.rtf':
                try:
                    from striprtf.striprtf import rtf_to_text
                    text = rtf_to_text(raw_bytes.decode('utf-8'))
                    return text
                except ImportError:
                    return f"INFO: La bibliothèque 'striprtf' est requise pour lire les fichiers RTF. Veuillez l'installer."
                except Exception as e:
                    return f"Erreur lors de la lecture du RTF {filename}: {str(e)}"
            
            # Pour TXT et MD
            try: 
                return raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    import chardet
                    detected = chardet.detect(raw_bytes)
                    encoding = detected.get('encoding', 'utf-8')
                    return raw_bytes.decode(encoding, errors='replace')
                except:
                    return raw_bytes.decode('cp1252', errors='replace')
                    
        except Exception as e: 
            return f"Erreur lors de la lecture du fichier texte {filename}: {str(e)}"

    def _read_code_file(self, file_stream, filename, file_ext):
        try:
            file_stream.seek(0)
            raw_bytes = file_stream.read()
            
            # Détection d'encodage pour fichiers code
            try:
                import chardet
                detected = chardet.detect(raw_bytes)
                encoding = detected.get('encoding', 'utf-8')
                content = raw_bytes.decode(encoding)
            except ImportError:
                content = raw_bytes.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                content = raw_bytes.decode('utf-8', errors='replace')
            
            # Formatage simple selon le type
            if file_ext == '.json':
                try:
                    import json
                    parsed = json.loads(content)
                    content = json.dumps(parsed, indent=2, ensure_ascii=False)
                except:
                    pass  # Garder le contenu original si parsing échoue
            
            elif file_ext in ['.yaml', '.yml']:
                try:
                    import yaml
                    parsed = yaml.safe_load(content)
                    content = yaml.dump(parsed, default_flow_style=False, allow_unicode=True)
                except:
                    pass  # Garder le contenu original si parsing échoue
            
            return content
            
        except Exception as e:
            return f"Erreur lors de la lecture du fichier code {filename}: {str(e)}"

    def _read_audio_file(self, file_bytes, filename, file_ext):
        """Lecture basique des métadonnées audio."""
        try:
            return f"Fichier audio: {filename}\nTaille: {len(file_bytes) / 1024 / 1024:.2f} MB\nFormat: {file_ext.upper()}\n\nNote: Analyse audio complète nécessite des bibliothèques spécialisées (pydub, librosa, speechrecognition)"
        except Exception as e:
            return f"Erreur lors de l'analyse audio {filename}: {str(e)}"

    def _read_image(self, file_bytes, filename, file_ext):
        try:
            img = Image.open(io.BytesIO(file_bytes))
            mime_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', 
                         '.gif': 'image/gif', '.bmp': 'image/bmp', '.webp': 'image/webp'}
            mime_type = mime_types.get(file_ext)
            if not mime_type: return f"Format d'image non supporté par l'API: {filename}"
            
            # Claude 3 image size limits: max 5MB per image, max 20MB per request, max 1568x1568 pixels
            if len(file_bytes) > 5 * 1024 * 1024: # 5MB
                return f"L'image {filename} dépasse la limite de 5MB par image."

            max_pixels = 1568 * 1568 
            if img.width * img.height > max_pixels:
                 print(f"Redimensionnement de l'image {filename} car elle dépasse la taille max de pixels ({img.width}x{img.height}).")
                 img.thumbnail((1568, 1568), Image.Resampling.LANCZOS)

            buffered = io.BytesIO()
            img_format = mime_type.split('/')[1].upper()
            if img_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                 print(f"Conversion de l'image {filename} en RGB pour sauvegarde JPEG.")
                 img = img.convert('RGB')
            
            # Save with quality settings if JPEG to control size a bit more
            if img_format == 'JPEG':
                img.save(buffered, format=img_format, quality=85, optimize=True)
            else:
                img.save(buffered, format=img_format)

            # Final check on encoded size
            if buffered.tell() > 5 * 1024 * 1024:
                 return f"L'image {filename} après encodage/redimensionnement dépasse toujours 5MB."

            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {'type': 'image', 'source': {'type': 'base64', 'media_type': mime_type, 'data': img_str}}
        except Exception as e: return f"Erreur lors du traitement de l'image {filename}: {str(e)}"

    def analyze_documents(self, uploaded_files, conversation_history):
        if not uploaded_files: return "Veuillez téléverser au moins un fichier.", []
        
        analysis_results, processed_contents, filenames, content_types = [], [], [], []
        total_image_size_mb = 0

        for uploaded_file in uploaded_files:
            content = self.read_file(uploaded_file)
            if isinstance(content, str) and (content.startswith("Erreur") or content.startswith("Format") or content.startswith("Aucun texte") or content.startswith("INFO") or content.startswith("Impossible") or content.startswith("L'image")):
                analysis_results.append((uploaded_file.name, content)) # Include error messages
            elif isinstance(content, dict) and content.get('type') == 'image':
                # Estimate size of base64 string for total request limit
                # Base64 is approx 4/3 original size. Add some overhead.
                image_size_bytes = len(content['source']['data']) * 3 / 4
                total_image_size_mb += image_size_bytes / (1024 * 1024)
                if total_image_size_mb > 18: # Leave some room for text and overhead from 20MB limit
                    analysis_results.append((uploaded_file.name, "Taille totale des images pour cette requête dépasserait la limite de l'API. Cette image n'a pas été ajoutée."))
                    continue # Skip this image
                processed_contents.append(content)
                filenames.append(uploaded_file.name)
                content_types.append('image')
            elif isinstance(content, str):
                 processed_contents.append(content)
                 filenames.append(uploaded_file.name)
                 content_types.append('text')
            else: 
                analysis_results.append((uploaded_file.name, f"Erreur interne: Type de contenu inattendu ({type(content)})"))

        if not processed_contents: 
            # If only errors, return them
            error_summary = "Aucun fichier n'a pu être traité avec succès pour l'analyse.\n"
            for name, reason in analysis_results:
                error_summary += f"- {name}: {reason}\n"
            return error_summary, analysis_results

        profile = self.get_current_profile()
        prompt_text_parts = [f"En tant qu'expert {profile['name']}, analysez le(s) contenu(s) suivant(s) provenant du/des fichier(s) nommé(s) : {', '.join(filenames)}."]
        history_str = self._format_history_for_api(conversation_history)
        if history_str != "Aucun historique": 
            prompt_text_parts.append(f"\nVoici l'historique récent de la conversation pour contexte:\n{SEPARATOR_SINGLE}\n{history_str}\n{SEPARATOR_SINGLE}")

        num_valid_files = len(processed_contents)
        
        if num_valid_files == 1:
            prompt_text_parts.append("\nAnalysez ce document/image et fournissez une analyse structurée comprenant :\n1.  **RÉSUMÉ / DESCRIPTION GÉNÉRALE:** Décrivez brièvement le contenu du fichier.\n2.  **ANALYSE TECHNIQUE / ÉLÉMENTS CLÉS:** Identifiez les points techniques, données, ou éléments visuels importants. S'il s'agit de plans ou schémas, décrivez-les.\n3.  **ANALYSE FINANCIÈRE (si applicable et possible):** Si des informations financières sont présentes ou peuvent être inférées, commentez-les.\n4.  **RECOMMANDATIONS / QUESTIONS:** Basé sur l'analyse, quelles sont vos recommandations ou quelles questions supplémentaires se posent ?")
        else:
            prompt_text_parts.append(f"\nAnalysez l'ensemble de ces documents/images et fournissez une synthèse intégrée :\n1.  **ANALYSE INDIVIDUELLE SUCCINCTE:** Pour chaque fichier ({', '.join(filenames)}), résumez son contenu principal et son type.\n2.  **POINTS COMMUNS ET DIVERGENCES:** Y a-t-il des thèmes, des données ou des informations qui se recoupent ou se contredisent entre les fichiers ?\n3.  **ANALYSE D'ENSEMBLE / SYNTHÈSE:** Quelle est la compréhension globale qui émerge de la combinaison de ces fichiers ?\n4.  **RECOMMANDATIONS INTÉGRÉES:** Quelles recommandations ou conclusions pouvez-vous tirer de l'ensemble des informations fournies ?")

        final_prompt_instruction = "\n".join(prompt_text_parts) + "\n\nFournissez votre réponse de manière claire et bien structurée."
        api_system_prompt = profile.get('content', 'Vous êtes un expert IA compétent.')
        
        user_message_content = []
        # Add images first as per Claude's best practices
        for i, content in enumerate(processed_contents):
            if content_types[i] == 'image': 
                user_message_content.append(content)
        
        # Then add text parts
        for i, content in enumerate(processed_contents):
             if content_types[i] == 'text':
                 user_message_content.append({"type": "text", "text": f"\n{SEPARATOR_DOUBLE}\nDEBUT Contenu Fichier: {filenames[i]}\n{SEPARATOR_SINGLE}\n{content}\n{SEPARATOR_SINGLE}\nFIN Contenu Fichier: {filenames[i]}\n{SEPARATOR_DOUBLE}\n"})
        
        # Add the final instruction
        user_message_content.append({"type": "text", "text": final_prompt_instruction})
        
        api_messages = [{"role": "user", "content": user_message_content}]

        try:
            print(f"Appel API Claude pour analyse de {num_valid_files} fichier(s)... Modèle: {self.model_name_global}")
            response = self.anthropic.messages.create(
                model=self.model_name_global, max_tokens=4000,
                messages=api_messages, system=api_system_prompt
            )
            if response.content and len(response.content) > 0 and response.content[0].text:
                api_response_text = response.content[0].text
                # Add successful analysis to results
                if num_valid_files > 0:
                    analysis_results.append(("Analyse Combinée" if num_valid_files > 1 else f"Analyse: {filenames[0]}", "Succès"))
                print("Analyse Claude terminée.")
                return api_response_text, analysis_results
            else:
                 error_msg = "Erreur: Réponse vide ou mal formée de l'API (analyse)."
                 print(error_msg)
                 if num_valid_files > 0:
                     analysis_results.append(("Erreur API Claude (Analyse)", error_msg))
                 return error_msg, analysis_results
        except APIError as e:
            error_msg = f"Erreur API Anthropic (analyse): {type(e).__name__} ({e.status_code}) - {e.message}"
            print(error_msg)
            if num_valid_files > 0:
                analysis_results.append(("Erreur API Claude (Analyse)", error_msg))
            return error_msg, analysis_results
        except Exception as e:
            error_msg = f"Erreur générique API (analyse): {type(e).__name__} - {str(e)}"
            print(error_msg)
            if num_valid_files > 0:
                analysis_results.append(("Erreur API Claude (Analyse)", error_msg))
            return error_msg, analysis_results

    def _format_history_for_api(self, conversation_history):
         if not conversation_history: return "Aucun historique"
         formatted_history = []
         turns_to_include = 5 # Number of user/assistant turn pairs
         
         # Iterate backwards to get the most recent turns
         user_turns = 0
         assistant_turns = 0
         temp_history = []
         for msg in reversed(conversation_history):
             if len(temp_history) >= turns_to_include * 2 : # Approx limit
                 break
             role, content = msg["role"], msg["content"]
             if role == "system": continue
             
             role_name = "Utilisateur" if role == "user" else "Expert"
             if role == "search_result": 
                 role_name = "InfoWeb"
                 content = f"[Résultat Recherche Web]: {content}"
             
             # Basic check for relevance, ignore very short/placeholder messages if needed
             # if len(str(content).strip()) < 10 and role != "user": continue 

             temp_history.append(f"{role_name}: {content}")

             if role == "user": user_turns +=1
             if role == "assistant": assistant_turns +=1
             if user_turns >= turns_to_include and assistant_turns >= turns_to_include:
                 break
        
         formatted_history = list(reversed(temp_history)) # Put back in chronological order
         return "\n".join(formatted_history) if formatted_history else "Aucun historique pertinent."

    def obtenir_reponse(self, question, conversation_history):
        profile = self.get_current_profile()
        if not profile: return "Erreur Critique: Profil expert non défini."
        
        api_messages_history = []
        # History for Claude API should be a list of {"role": "user/assistant", "content": ...}
        # Include a limited number of recent messages
        history_limit_pairs = 8 # Max user/assistant pairs
        
        # Filter and format history
        relevant_history = []
        for msg in conversation_history:
            role, content = msg.get("role"), msg.get("content")
            if role == "system" or not isinstance(content, str): # Skip system messages and non-string content for this
                continue
            
            # Map roles correctly for Claude
            api_role = None
            if role == "user":
                api_role = "user"
            elif role == "assistant" or role == "search_result":
                api_role = "assistant"
                if role == "search_result":
                    content = f"[Info from Web Search]:\n{content}"
            
            if api_role:
                relevant_history.append({"role": api_role, "content": content})
        
        # Take last N messages, ensuring it starts with user if possible, or just truncates
        start_index = max(0, len(relevant_history) - (history_limit_pairs * 2))
        api_messages_history = relevant_history[start_index:]

        api_messages_history.append({"role": "user", "content": question})
        
        api_system_prompt = profile.get('content', 'Vous êtes un expert IA utile.')
        
        try:
            print(f"Appel API Claude pour réponse conversationnelle... Modèle: {self.model_name_global}")
            response = self.anthropic.messages.create(
                model=self.model_name_global, 
                max_tokens=4000,
                messages=api_messages_history, 
                system=api_system_prompt
            )
            if response.content and len(response.content) > 0 and response.content[0].text:
                print("Réponse Claude reçue.")
                return response.content[0].text
            else:
                 print("Erreur: Réponse vide ou mal formée de l'API (obtenir_reponse).")
                 return "Désolé, j'ai reçu une réponse vide de l'IA Claude. Veuillez réessayer."
        except APIError as e:
            print(f"Erreur API Anthropic (obtenir_reponse): {type(e).__name__} ({e.status_code}) - {e.message}")
            return f"Désolé, une erreur API technique est survenue avec l'IA Claude ({e.status_code}). Veuillez réessayer."
        except Exception as e:
            print(f"API Error (Claude) in obtenir_reponse: {type(e).__name__} - {e}")
            return f"Désolé, une erreur technique est survenue avec l'IA Claude ({type(e).__name__}). Veuillez réessayer."

    def perform_web_search(self, query: str) -> str:
        """Effectue une recherche web RÉELLE via l'API Claude et retourne la synthèse des résultats."""
        if not query:
            return "Erreur: La requête de recherche est vide."
        
        print(f"[WEB] Recherche web RÉELLE pour: '{query}'")
        
        try:
            # Configuration des outils de recherche web - INSPIRÉ DU SCRIPT GRADIO QUI FONCTIONNE
            tools = [{
                "type": "web_search_20250305",
                "name": "web_search",
                "user_location": {
                    "type": "approximate",
                    "city": "Rougemont",  # Ou adaptez selon votre localisation au Québec
                    "region": "Quebec",
                    "country": "CA",
                    "timezone": "America/Montreal"
                }
            }]
            
            print(f"[WEB] Envoi de la requête à Claude avec recherche web activée...")
            
            # Utiliser claude-opus-4-1-20250805 comme dans le script qui fonctionne
            # OU garder votre modèle actuel si vous préférez
            response = self.anthropic.messages.create(
                model="claude-opus-4-1-20250805",  # Modèle du script qui fonctionne
                max_tokens=4000,
                temperature=0.1,  # Plus bas pour des résultats factuels
                messages=[{
                    "role": "user", 
                    "content": f"Effectue une recherche web pour: {query}. Fournis une réponse détaillée basée sur les informations trouvées."
                }],
                tools=tools  # AJOUT DES OUTILS - C'ÉTAIT LE PROBLÈME PRINCIPAL
            )
            
            print(f"[WEB] Réponse reçue de Claude")
            
            # Analyser la réponse - INSPIRÉ DU SCRIPT GRADIO
            if hasattr(response, 'content') and response.content:
                search_performed = False
                search_results_found = False
                final_text = ""
                
                # Parcourir tous les blocs de contenu
                for i, block in enumerate(response.content):
                    if hasattr(block, 'type'):
                        block_type = getattr(block, 'type')
                        print(f"[WEB] Bloc {i}: Type = {block_type}")
                        
                        # Détecter si une recherche web a été effectuée
                        if block_type == 'server_tool_use' and getattr(block, 'name', '') == 'web_search':
                            search_performed = True
                            print(f"[WEB] ✅ Recherche web détectée dans bloc {i}")
                        
                        # Détecter les résultats de recherche
                        elif block_type == 'web_search_tool_result':
                            search_results_found = True
                            print(f"[WEB] ✅ Résultats de recherche trouvés dans bloc {i}")
                        
                        # Récupérer le texte de la réponse
                        elif block_type == 'text' and hasattr(block, 'text'):
                            text = block.text
                            final_text += text + "\n\n"
                
                # Diagnostic et retour
                if search_performed:
                    if search_results_found:
                        print(f"[WEB] 🎉 SUCCÈS: Recherche web réelle effectuée!")
                        if final_text:
                            print(f"[WEB] Réponse obtenue, longueur: {len(final_text)} caractères")
                            return final_text.strip()
                        else:
                            return "La recherche web a été effectuée mais aucun texte de réponse n'a été généré."
                    else:
                        print(f"[WEB] ⚠️ Recherche tentée mais pas de résultats retournés")
                        return "Une recherche web a été tentée mais aucun résultat n'a été retourné."
                else:
                    print(f"[WEB] ❌ ÉCHEC: Aucune recherche web effectuée")
                    # Retourner quand même le texte s'il y en a un (réponse basée sur connaissances)
                    if final_text:
                        return f"⚠️ Réponse basée sur les connaissances internes (pas de recherche web):\n\n{final_text.strip()}"
                    else:
                        return "Aucune recherche web n'a été effectuée et aucune réponse n'a été générée."
            else:
                print(f"[WEB] ⚠️ Aucun contenu dans la réponse")
                return "La recherche n'a pas produit de contenu. Vérifiez votre requête."
                    
        except APIError as e:
            error_message = f"Erreur API Anthropic lors de la recherche web ({e.status_code}): {e.message}"
            print(f"[WEB] {error_message}")
            
            # Messages d'erreur plus informatifs selon le code d'erreur
            if e.status_code == 401:
                return "❌ Erreur d'authentification: Vérifiez votre clé API Anthropic."
            elif e.status_code == 403:
                return "❌ Accès refusé: Votre clé API n'a peut-être pas accès à la recherche web. Vérifiez vos permissions dans la console Anthropic."
            elif e.status_code == 429:
                return "❌ Limite de taux dépassée: Trop de requêtes. Attendez un moment avant de réessayer."
            else:
                return f"❌ Erreur API ({e.status_code}): {e.message}"
                
        except Exception as e:
            print(f"[WEB] Erreur générique lors de la recherche: {type(e).__name__} - {str(e)}")
            import traceback
            traceback.print_exc()
            return f"❌ Erreur technique lors de la recherche web: {type(e).__name__}. Veuillez réessayer."

# --- FIN CLASSE ExpertAdvisor ---