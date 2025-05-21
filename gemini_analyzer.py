```python
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
from google.generativeai import types
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

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
        self.chat_history = []  # Speichert den Chatverlauf für Folgefragen
        if self.api_key != "DUMMY_API_KEY_FOR_TESTING":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.chat = None # Will be initialized in analyze or ask_followup_question
            logger.info(f"GeminiAnalyzer initialisiert mit Modell: {self.model_name}")
        else:
            self.model = None # No actual model needed for mocking
            logger.info(f"GeminiAnalyzer initialisiert im MOCK-MODUS mit Modell: {self.model_name}")


    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _prepare_prompt(self, data: Dict[str, Any], analysis_type: str = "standard") -> str:
        if analysis_type == "standard":
            prompt = f"""
            Analysiere diese Kleinanzeige und erstelle einen detaillierten Bericht.

            Titel: {data.get('title', 'Nicht angegeben')}
            Preis: {data.get('price', 'Nicht angegeben')} €
            Beschreibung: {data.get('description', 'Keine Beschreibung vorhanden')}

            Details:
            """

            if data.get('details'):
                for key, value in data['details'].items():
                    prompt += f"- {key}: {value}\n"
            else:
                prompt += "Keine Details vorhanden.\n"

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

            prompt += "\nStandort:\n"
            if data.get('location') and data['location'].get('address'):
                prompt += f"- Adresse: {data['location']['address']}\n"
            else:
                prompt += "Keine Standortinformationen vorhanden.\n"

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
            return "Bitte analysiere diese Kleinanzeige."

    def analyze(self, data: Dict[str, Any], image_paths: List[str], analysis_type: str = "standard") -> Dict[str, Any]:
        """
        Analysiert die Kleinanzeigen-Daten mit dem Gemini-Modell.
        """
        prompt = self._prepare_prompt(data, analysis_type)
        analysis_text = "" # Initialize analysis_text
        current_time = datetime.now().isoformat()

        if self.api_key == "DUMMY_API_KEY_FOR_TESTING":
            logger.info(f"MOCK-ANALYSE für Daten: {data.get('title')}")
            analysis_text = f"Dies ist eine MOCK-Analyse für '{data.get('title', 'Unbekannte Anzeige')}'.\n\n1. Zusammenfassung: Mock-Zusammenfassung.\n2. Preis: Mock-Preisbewertung.\n3. Verkäufer: Mock-Verkäuferseriosität.\n4. Warnzeichen: Keine Mock-Warnzeichen.\n5. Empfehlungen: Mock-Empfehlungen."
            logger.info(f"Mock-Analyse-Text generiert, Länge: {len(analysis_text)} Zeichen")
            
        else: # Real API call logic
            try:
                contents = [prompt]
                # from google.generativeai import types # Already imported at the top
                for i, img_path in enumerate(image_paths[:3]):
                    try:
                        with open(img_path, 'rb') as f:
                            image_bytes = f.read()
                        image_part = types.Part.from_data(
                            mime_type=self._get_mime_type(img_path),
                            data=image_bytes
                        )
                        contents.append(image_part)
                        logger.info(f"Bild hinzugefügt: {img_path}")
                    except Exception as e:
                        logger.error(f"Fehler beim Hinzufügen des Bildes {img_path}: {str(e)}")
                
                self.chat = self.model.start_chat(history=[]) 
                response = self.chat.send_message(contents)
                analysis_text = response.text

                analysis_text = analysis_text.strip()
                if not (analysis_text.startswith("<p>") and analysis_text.endswith("</p>")):
                    analysis_text = analysis_text.replace("\n\n", "\n\n")
                logger.info(f"Analyse-Text erfolgreich extrahiert, Länge: {len(analysis_text)} Zeichen")

            except Exception as e:
                logger.error(f"Fehler bei der Analyse: {str(e)}")
                if 'prompt' not in locals(): 
                    prompt = "Error during prompt generation for analysis." 
                self.chat_history = [
                    {"role": "user", "parts": [{"text": prompt}]},
                    {"role": "model", "parts": [{"text": f"Fehler bei der Analyse: {str(e)}"}]}
                ]
                return {
                    "success": False,
                    "error": str(e),
                    "model": self.model_name,
                    "analyzed_at": current_time,
                    "chat_history": self.chat_history 
                }

        self.chat_history = [
            {"role": "user", "parts": [{"text": prompt}]},
            {"role": "model", "parts": [{"text": analysis_text}]}
        ]

        result = {
            "success": True,
            "analysis": analysis_text,
            "model": self.model_name,
            "analyzed_at": current_time,
            "chat_history": self.chat_history
        }
        logger.info(f"Analyse MOCK/ERFOLGREICH abgeschlossen. Zurückgegebenes Resultat: success={result.get('success')}, model={result.get('model')}, chat_history_len={len(result.get('chat_history', []))}")
        return result

    def _get_mime_type(self, file_path: str) -> str:
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

    def ask_followup_question(self, question: str, ad_id: str, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        from datetime import datetime # Ensure datetime is imported
        current_time = datetime.now().isoformat()

        if self.api_key == "DUMMY_API_KEY_FOR_TESTING":
            logger.info(f"MOCK-FOLGEFRAGE für Ad ID {ad_id}: '{question}'")
            answer_text = f"Mocked Antwort für '{question}'. Marke: {scraped_data.get('details', {}).get('Marke', 'N/A')}."
            
            self.chat_history.append({"role": "user", "parts": [{"text": question}]})
            self.chat_history.append({"role": "model", "parts": [{"text": answer_text}]})
            
            logger.info(f"Mock-Antwort generiert. Chat-Länge: {len(self.chat_history)}")
            return {
                "success": True,
                "question": question,
                "answer": answer_text,
                "model": self.model_name,
                "asked_at": current_time,
                "chat_history": self.chat_history
            }
        else:
            # Real API call logic
            try:
                if not hasattr(self, 'chat') or self.chat is None: 
                    logger.info("Chat-Objekt existiert nicht, versuche aus Verlauf wiederherzustellen.")
                    self.chat = self.model.start_chat(history=[]) 
                    if self.chat_history:
                        formatted_history = []
                        for entry in self.chat_history:
                            parts_list = []
                            for part_item in entry.get("parts", []):
                                if isinstance(part_item, dict) and "text" in part_item:
                                    parts_list.append(types.Part.from_text(part_item["text"]))
                            if parts_list: 
                                 formatted_history.append(types.Content(parts=parts_list, role=entry["role"]))
                        if formatted_history: 
                            self.chat = self.model.start_chat(history=formatted_history)

                context_prompt = f"""
                Kontext: Titel: {scraped_data.get('title', 'N/A')}, Preis: {scraped_data.get('price', 'N/A')}, Beschreibung: {scraped_data.get('description', 'N/A')}
                Details: {scraped_data.get('details', {})}
                Verkäufer: {scraped_data.get('seller', {})}
                Standort: {scraped_data.get('location', {}).get('address', 'N/A')}
                """
                
                response = self.chat.send_message(f"{context_prompt}\n\nFrage: {question}")
                answer_text = response.text

                updated_history = []
                for hist_entry in self.chat.history:
                    parts_list = []
                    for part in hist_entry.parts: 
                        if hasattr(part, 'text'):
                            parts_list.append({"text": part.text})
                    updated_history.append({"role": hist_entry.role, "parts": parts_list})
                self.chat_history = updated_history

                result = {
                    "success": True,
                    "question": question,
                    "answer": answer_text,
                    "model": self.model_name,
                    "asked_at": current_time,
                    "chat_history": self.chat_history
                }

                logger.info(f"Folgefrage erfolgreich beantwortet, Länge der Antwort: {len(answer_text)} Zeichen. Chat-Länge: {len(self.chat_history)}")
                return result

            except Exception as e:
                logger.error(f"Fehler bei der Beantwortung der Folgefrage: {str(e)}")
                # Ensure self.chat_history is updated with the user's question even if there's an error
                # so the UI can reflect the attempt.
                # Only add the question if it's not already the last message (to avoid duplicates if send_message failed early)
                if not self.chat_history or self.chat_history[-1].get("parts")[0].get("text") != question:
                     self.chat_history.append({"role": "user", "parts": [{"text": question}]})
                self.chat_history.append({"role": "model", "parts": [{"text": f"Error processing your question: {str(e)}"}]})
                return {
                    "success": False,
                    "question": question,
                    "error": str(e),
                    "model": self.model_name,
                    "asked_at": current_time,
                    "chat_history": self.chat_history 
                }


# Hilfsfunktion zum Speichern der Analyseergebnisse
def save_analysis_result(ad_id: str, analysis_result: Dict[str, Any], output_dir: str = "output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{ad_id}_analysis.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)

    logger.info(f"Analyseergebnis gespeichert: {filepath}")
    return filepath

# Hilfsfunktion zum Speichern der Folgefragen und Antworten
def save_chat_history(ad_id: str, chat_result: Dict[str, Any], output_dir: str = "output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{ad_id}_chat.json"
    filepath = os.path.join(output_dir, filename)

    # Determine the correct timestamp key based on what's available in chat_result
    timestamp = chat_result.get('asked_at') or chat_result.get('analyzed_at')

    # Prepare the data to be saved
    chat_data_to_save = {
        'ad_id': ad_id,
        'model': chat_result.get('model'),
        'chat_history': chat_result.get('chat_history', []), # Use the chat_history from the result
        'last_updated': timestamp
    }

    # If the file doesn't exist, it's the first time saving, so set 'created_at'
    if not os.path.exists(filepath):
        chat_data_to_save['created_at'] = timestamp
    else:
        # If it exists, load existing data to preserve 'created_at'
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            chat_data_to_save['created_at'] = existing_data.get('created_at', timestamp) # Keep original or set if missing
        except FileNotFoundError:
             # This can happen if save_analysis_result created the directory but not the file yet,
             # or if another process deleted it.
             chat_data_to_save['created_at'] = timestamp


    # Write the updated chat data
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(chat_data_to_save, f, ensure_ascii=False, indent=2)

    logger.info(f"Chatverlauf gespeichert: {filepath}")
    return filepath
```
Now that `gemini_analyzer.py` is corrected, I'll restart the Flask app and proceed with the initial analysis test again.
