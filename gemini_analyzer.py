#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini Analyzer Module

Dieses Modul stellt Funktionen zur Analyse von Kleinanzeigen-Daten mit dem Gemini 2.5 Pro Modell bereit.
"""

import os
import json
import base64
from google import genai
from typing import Dict, List, Any, Optional
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    """Klasse zur Analyse von Kleinanzeigen-Daten mit dem Gemini 2.5 Pro Modell."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        Initialisiert den Gemini Analyzer.

        Args:
            api_key (str): Der API-Schlüssel für die Gemini API
            model_name (str, optional): Der Name des zu verwendenden Modells. Standardmäßig "gemini-2.0-flash".
        """
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)
        self.chat_history = []  # Speichert den Chatverlauf für Folgefragen
        logger.info(f"GeminiAnalyzer initialisiert mit Modell: {model_name}")

    def _encode_image(self, image_path: str) -> str:
        """
        Kodiert ein Bild als Base64-String.

        Args:
            image_path (str): Der Pfad zum Bild

        Returns:
            str: Der Base64-kodierte String des Bildes
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _prepare_prompt(self, data: Dict[str, Any], analysis_type: str = "standard") -> str:
        """
        Bereitet den Prompt für die Analyse vor.

        Args:
            data (Dict[str, Any]): Die Kleinanzeigen-Daten
            analysis_type (str, optional): Der Typ der Analyse. Standardmäßig "standard".

        Returns:
            str: Der vorbereitete Prompt
        """
        if analysis_type == "standard":
            prompt = f"""
            Analysiere diese Kleinanzeige und erstelle einen detaillierten Bericht.

            Titel: {data.get('title', 'Nicht angegeben')}
            Preis: {data.get('price', 'Nicht angegeben')} €
            Beschreibung: {data.get('description', 'Keine Beschreibung vorhanden')}

            Details:
            """

            # Details hinzufügen
            if data.get('details'):
                for key, value in data['details'].items():
                    prompt += f"- {key}: {value}\n"
            else:
                prompt += "Keine Details vorhanden.\n"

            # Verkäuferinformationen hinzufügen
            prompt += "\nVerkäuferinformationen:\n"
            if data.get('seller'):
                seller = data['seller']
                prompt += f"- Name: {seller.get('name', 'Nicht angegeben')}\n"
                prompt += f"- Typ: {seller.get('type', 'Nicht angegeben')}\n"
                prompt += f"- Mitglied seit: {seller.get('member_since', 'Nicht angegeben')}\n"

                if seller.get('badges'):
                    prompt += "- Badges: " + ", ".join(seller['badges']) + "\n"

                if seller.get('profile'):
                    profile = seller['profile']
                    if profile.get('rating_percentage'):
                        prompt += f"- Bewertung: {profile.get('rating_percentage')}% ({profile.get('reviews_count', '0')} Bewertungen)\n"
                    if profile.get('response_time'):
                        prompt += f"- Antwortzeit: {profile.get('response_time')}\n"
            else:
                prompt += "Keine Verkäuferinformationen vorhanden.\n"

            # Standort hinzufügen
            prompt += "\nStandort:\n"
            if data.get('location') and data['location'].get('address'):
                prompt += f"- Adresse: {data['location']['address']}\n"
            else:
                prompt += "Keine Standortinformationen vorhanden.\n"

            # Anweisungen für die Analyse
            prompt += """
            Bitte analysiere diese Anzeige und erstelle einen Bericht mit folgenden Punkten:
            1. Zusammenfassung des Angebots
            2. Bewertung des Preis-Leistungs-Verhältnisses (falls möglich)
            3. Einschätzung der Seriosität des Verkäufers
            4. Auffälligkeiten oder Warnzeichen
            5. Empfehlungen für potenzielle Käufer

            Beziehe die Bilder in deine Analyse mit ein und beschreibe, was auf ihnen zu sehen ist und ob sie mit der Beschreibung übereinstimmen.
            """

            return prompt
        else:
            # Andere Analysetypen können hier implementiert werden
            return "Bitte analysiere diese Kleinanzeige."

    def analyze(self, data: Dict[str, Any], image_paths: List[str], analysis_type: str = "standard") -> Dict[str, Any]:
        """
        Analysiert die Kleinanzeigen-Daten mit dem Gemini-Modell.

        Args:
            data (Dict[str, Any]): Die Kleinanzeigen-Daten
            image_paths (List[str]): Liste der Pfade zu den Bildern
            analysis_type (str, optional): Der Typ der Analyse. Standardmäßig "standard".

        Returns:
            Dict[str, Any]: Das Analyseergebnis
        """
        try:
            # Prompt vorbereiten
            prompt = self._prepare_prompt(data, analysis_type)

            # Inhalte für die Anfrage vorbereiten
            contents = [prompt]

            # Bilder hinzufügen (maximal 3 Bilder, um die Anfragegröße zu begrenzen)
            from google.genai import types

            for i, img_path in enumerate(image_paths[:3]):  # Begrenze auf 3 Bilder
                try:
                    with open(img_path, 'rb') as f:
                        image_bytes = f.read()

                    image_part = types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=self._get_mime_type(img_path)
                    )

                    contents.append(image_part)
                    logger.info(f"Bild hinzugefügt: {img_path}")
                except Exception as e:
                    logger.error(f"Fehler beim Hinzufügen des Bildes {img_path}: {str(e)}")

            # Anfrage an Gemini senden gemäß der aktuellen API-Dokumentation
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )

            # Antwort verarbeiten
            from datetime import datetime

            # Prüfen, ob die Antwort erfolgreich war
            if hasattr(response, 'text'):
                analysis_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                analysis_text = response.candidates[0].content.parts[0].text
            else:
                analysis_text = "Keine Analyseergebnisse verfügbar."

            # Entfernen von HTML-Tags am Anfang und Ende, falls vorhanden
            analysis_text = analysis_text.strip()
            if analysis_text.startswith("<p>") and analysis_text.endswith("</p>"):
                # Wenn der Text bereits HTML-formatiert ist, belassen wir ihn so
                pass
            else:
                # Ansonsten formatieren wir den Text als Markdown
                # Wir ersetzen doppelte Zeilenumbrüche durch Markdown-Absätze
                analysis_text = analysis_text.replace("\n\n", "\n\n")

            logger.info(f"Analyse-Text erfolgreich extrahiert, Länge: {len(analysis_text)} Zeichen")

            # Chatverlauf initialisieren - wir speichern nur die Anfrage,
            # da die Analyse bereits als erste Nachricht im Chat-Interface angezeigt wird
            self.chat_history = [
                {"role": "user", "content": f"Analysiere diese Kleinanzeige: {data.get('title', 'Unbekannte Anzeige')}"}
            ]

            result = {
                "success": True,
                "analysis": analysis_text,
                "model": self.model_name,
                "analyzed_at": datetime.now().isoformat(),
                "chat_history": self.chat_history
            }

            logger.info("Analyse erfolgreich abgeschlossen")
            return result

        except Exception as e:
            logger.error(f"Fehler bei der Analyse: {str(e)}")
            from datetime import datetime
            return {
                "success": False,
                "error": str(e),
                "model": self.model_name,
                "analyzed_at": datetime.now().isoformat(),
            }

    def _get_mime_type(self, file_path: str) -> str:
        """
        Ermittelt den MIME-Typ einer Datei anhand ihrer Erweiterung.

        Args:
            file_path (str): Der Pfad zur Datei

        Returns:
            str: Der MIME-Typ der Datei
        """
        extension = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.heic': 'image/heic',
            '.heif': 'image/heif',
        }
        return mime_types.get(extension, 'application/octet-stream')

    def ask_followup_question(self, question: str, ad_id: str) -> Dict[str, Any]:
        """
        Stellt eine Folgefrage an das Gemini-Modell basierend auf dem bisherigen Chatverlauf.

        Args:
            question (str): Die Folgefrage des Benutzers
            ad_id (str): Die ID der Anzeige, auf die sich die Frage bezieht

        Returns:
            Dict[str, Any]: Das Ergebnis der Folgefrage
        """
        try:
            # Frage zum Chatverlauf hinzufügen
            self.chat_history.append({"role": "user", "content": question})

            # Anfrage an Gemini senden
            # Wir fügen die Analyse als Kontext hinzu, falls sie nicht im Chatverlauf ist
            has_analysis_in_history = any(msg.get("role") == "assistant" for msg in self.chat_history)

            if not has_analysis_in_history:
                # Analyse-Datei lesen, um den Analysetext zu erhalten
                try:
                    import os
                    import json
                    analysis_path = os.path.join('output', f'{ad_id}_analysis.json')
                    if os.path.exists(analysis_path):
                        with open(analysis_path, 'r', encoding='utf-8') as f:
                            analysis_data = json.load(f)
                            analysis_text = analysis_data.get('analysis', '')

                            # Analyse als erste Assistenten-Nachricht hinzufügen
                            contents = [
                                {"role": "user", "content": f"Ich stelle dir Fragen zu einer Kleinanzeige mit der ID {ad_id}. Du hast bereits eine Analyse erstellt. Bitte beantworte meine Fragen basierend auf dieser Analyse und deinem Wissen."},
                                {"role": "assistant", "content": analysis_text},
                                *self.chat_history
                            ]
                    else:
                        contents = [
                            {"role": "user", "content": f"Ich stelle dir Fragen zu einer Kleinanzeige mit der ID {ad_id}. Bitte beantworte meine Fragen basierend auf den Informationen, die du bereits über diese Anzeige hast."},
                            *self.chat_history
                        ]
                except Exception as e:
                    logger.error(f"Fehler beim Laden der Analyse: {str(e)}")
                    contents = [
                        {"role": "user", "content": f"Ich stelle dir Fragen zu einer Kleinanzeige mit der ID {ad_id}. Bitte beantworte meine Fragen basierend auf den Informationen, die du bereits über diese Anzeige hast."},
                        *self.chat_history
                    ]
            else:
                contents = [
                    {"role": "user", "content": f"Ich stelle dir Fragen zu einer Kleinanzeige mit der ID {ad_id}. Bitte beantworte meine Fragen basierend auf den Informationen, die du bereits über diese Anzeige hast."},
                    *self.chat_history
                ]

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )

            # Antwort verarbeiten
            from datetime import datetime

            # Prüfen, ob die Antwort erfolgreich war
            if hasattr(response, 'text'):
                answer_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                answer_text = response.candidates[0].content.parts[0].text
            else:
                answer_text = "Keine Antwort verfügbar."

            # Antwort zum Chatverlauf hinzufügen
            self.chat_history.append({"role": "assistant", "content": answer_text})

            # Ergebnis zurückgeben
            result = {
                "success": True,
                "question": question,
                "answer": answer_text,
                "model": self.model_name,
                "asked_at": datetime.now().isoformat(),
                "chat_history": self.chat_history
            }

            logger.info(f"Folgefrage erfolgreich beantwortet, Länge der Antwort: {len(answer_text)} Zeichen")
            return result

        except Exception as e:
            logger.error(f"Fehler bei der Beantwortung der Folgefrage: {str(e)}")
            from datetime import datetime
            return {
                "success": False,
                "question": question,
                "error": str(e),
                "model": self.model_name,
                "asked_at": datetime.now().isoformat()
            }


# Hilfsfunktion zum Speichern der Analyseergebnisse
def save_analysis_result(ad_id: str, analysis_result: Dict[str, Any], output_dir: str = "output") -> str:
    """
    Speichert das Analyseergebnis als JSON-Datei.

    Args:
        ad_id (str): Die ID der Anzeige
        analysis_result (Dict[str, Any]): Das Analyseergebnis
        output_dir (str, optional): Das Ausgabeverzeichnis. Standardmäßig "output".

    Returns:
        str: Der Pfad zur gespeicherten Datei
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{ad_id}_analysis.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)

    logger.info(f"Analyseergebnis gespeichert: {filepath}")
    return filepath

# Hilfsfunktion zum Speichern der Folgefragen und Antworten
def save_chat_history(ad_id: str, chat_result: Dict[str, Any], output_dir: str = "output") -> str:
    """
    Speichert den Chatverlauf als JSON-Datei.

    Args:
        ad_id (str): Die ID der Anzeige
        chat_result (Dict[str, Any]): Das Ergebnis der Folgefrage
        output_dir (str, optional): Das Ausgabeverzeichnis. Standardmäßig "output".

    Returns:
        str: Der Pfad zur gespeicherten Datei
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{ad_id}_chat.json"
    filepath = os.path.join(output_dir, filename)

    # Prüfen, ob bereits ein Chat existiert
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)

        # Neuen Chat-Eintrag hinzufügen
        chat_data['chat_history'] = chat_result.get('chat_history', [])
        chat_data['last_updated'] = chat_result.get('asked_at')
    else:
        # Neue Chat-Datei erstellen
        chat_data = {
            'ad_id': ad_id,
            'model': chat_result.get('model'),
            'chat_history': chat_result.get('chat_history', []),
            'created_at': chat_result.get('asked_at'),
            'last_updated': chat_result.get('asked_at')
        }

    # Datei speichern
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Chatverlauf gespeichert: {filepath}")
    return filepath
