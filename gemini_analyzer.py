#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini Analyzer Module

Dieses Modul stellt Funktionen zur Analyse von Kleinanzeigen-Daten mit dem Gemini 2.5 Pro Modell bereit.
"""

import os
import json # Added for ad_data serialization in create_chat_engine
import base64
from google import genai # Retained for initial analysis
from typing import Dict, List, Any, Optional
import logging

# LlamaIndex Imports
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.gemini import Gemini as LlamaGemini # Renamed to avoid conflict
from llama_index.embeddings.gemini import GeminiEmbedding

# Logging konfigurieren
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s') # Already configured
logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    """Klasse zur Analyse von Kleinanzeigen-Daten mit dem Gemini 2.5 Pro Modell."""

    def __init__(self, api_key: str, model_name: str = "gemini-pro"): # Changed default model for genai
        """
        Initialisiert den Gemini Analyzer.

        Args:
            api_key (str): Der API-Schlüssel für die Gemini API
            model_name (str, optional): Der Name des zu verwendenden Modells für die initiale Analyse.
                                      Standardmäßig "gemini-pro". Für LlamaIndex wird "gemini-pro" oder "gemini-1.5-flash" verwendet.
        """
        self.api_key = api_key
        self.model_name = model_name # For initial analysis using google.genai

        # Client for initial analysis (using google.genai)
        self.client = genai.Client(api_key=api_key)
        logger.info(f"GeminiAnalyzer initialisiert mit google.genai Modell: {model_name}")

        # LlamaIndex Settings
        try:
            self.llm = LlamaGemini(api_key=self.api_key, model_name="gemini-pro") # Default for LlamaIndex chat
            self.embed_model = GeminiEmbedding(api_key=self.api_key, model_name="models/embedding-001")

            Settings.llm = self.llm
            Settings.embed_model = self.embed_model
            Settings.chunk_size = 512
            Settings.chunk_overlap = 20
            logger.info(f"LlamaIndex Settings konfiguriert mit LLM: {self.llm.model_name} und Embed Model: {self.embed_model.model_name}")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der LlamaIndex Settings: {str(e)}")
            # Potentially raise an error or set a flag indicating LlamaIndex features are unavailable

        # self.chat_history = [] # Removed, LlamaIndex chat engine will manage its own history

    def _encode_image(self, image_path: str) -> str:
        """
        Kodiert ein Bild als Base64-String. (Beibehalten für potenzielle zukünftige Nutzung, auch wenn Gemini-Vision-Modelle direktere Wege bevorzugen)

        Args:
            image_path (str): Der Pfad zum Bild

        Returns:
            str: Der Base64-kodierte String des Bildes
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _prepare_prompt(self, data: Dict[str, Any], analysis_type: str = "standard") -> str:
        """
        Bereitet den Prompt für die initiale Analyse vor. (Beibehalten für `analyze` Methode)
        """
        # ... (existing _prepare_prompt logic remains unchanged) ...
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
        Analysiert die Kleinanzeigen-Daten mit dem google.genai Client für die initiale Bewertung. (Beibehalten)
        """
        # ... (existing analyze logic using self.client remains largely unchanged) ...
        # Important: This method uses self.client (google.genai) not LlamaIndex
        try:
            prompt = self._prepare_prompt(data, analysis_type)
            contents = [prompt]
            from google.genai import types # Ensure this import is still here

            for i, img_path in enumerate(image_paths[:3]):
                try:
                    with open(img_path, 'rb') as f:
                        image_bytes = f.read()
                    image_part = types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=self._get_mime_type(img_path)
                    )
                    contents.append(image_part)
                    logger.info(f"Bild hinzugefügt für initiale Analyse: {img_path}")
                except Exception as e:
                    logger.error(f"Fehler beim Hinzufügen des Bildes {img_path} für initiale Analyse: {str(e)}")

            response = self.client.generate_content( # Corrected: was self.client.models.generate_content
                model=self.model_name,
                contents=contents
            )
            from datetime import datetime

            if hasattr(response, 'text'):
                analysis_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                analysis_text = response.candidates[0].content.parts[0].text
            else:
                analysis_text = "Keine Analyseergebnisse verfügbar."

            analysis_text = analysis_text.strip()
            # Initial chat history for the LlamaIndex engine might be set up differently or not needed here.
            # The main output is analysis_text.

            logger.info(f"Initiale Analyse-Text erfolgreich extrahiert, Länge: {len(analysis_text)} Zeichen")
            result = {
                "success": True,
                "analysis": analysis_text,
                "model": self.model_name, # This is the model from google.genai
                "analyzed_at": datetime.now().isoformat(),
                # "chat_history" is removed from here, will be managed by LlamaIndex engine
            }
            logger.info("Initiale Analyse erfolgreich abgeschlossen")
            return result
        except Exception as e:
            logger.error(f"Fehler bei der initialen Analyse: {str(e)}")
            from datetime import datetime
            return {
                "success": False,
                "error": str(e),
                "model": self.model_name,
                "analyzed_at": datetime.now().isoformat(),
            }

    def _get_mime_type(self, file_path: str) -> str:
        """
        Ermittelt den MIME-Typ einer Datei anhand ihrer Erweiterung. (Beibehalten)
        """
        # ... (existing _get_mime_type logic remains unchanged) ...
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

    def create_chat_engine(self, ad_data: dict, initial_analysis_text: str):
        """
        Erstellt eine LlamaIndex Chat-Engine basierend auf den Anzeigendaten und der initialen Analyse.
        """
        logger.info("Erstelle LlamaIndex Chat Engine...")
        try:
            # Ensure LlamaIndex settings are applied (should be done in __init__)
            # If self.llm or self.embed_model failed in __init__, this might error or use defaults
            if not Settings.llm or not Settings.embed_model:
                 logger.warning("LlamaIndex LLM oder Embed Model nicht in Settings initialisiert. Chat Engine Erstellung könnte fehlschlagen.")
                 # Optionally, re-attempt initialization or raise an error
                 # Settings.llm = self.llm
                 # Settings.embed_model = self.embed_model

            # More detailed ad text representation
            ad_details_str = "\n".join([f"- {k}: {v}" for k, v in ad_data.get('details', {}).items()])
            seller_profile = ad_data.get('seller', {}).get('profile', {})
            seller_profile_str = "\n".join([f"- {k}: {v}" for k, v in seller_profile.items()])

            ad_text = f"""Scraped Ad Data:
Title: {ad_data.get('title', 'N/A')}
Price: {ad_data.get('price', 'N/A')}
Description:
{ad_data.get('description', 'N/A')}

Details:
{ad_details_str if ad_details_str else 'N/A'}

Seller Information:
Name: {ad_data.get('seller', {}).get('name', 'N/A')}
Type: {ad_data.get('seller', {}).get('type', 'N/A')}
Member Since: {ad_data.get('seller', {}).get('member_since', 'N/A')}
Badges: {', '.join(ad_data.get('seller', {}).get('badges', []))}
Active Ads Count (on ad page): {ad_data.get('seller', {}).get('active_ads_count', 'N/A')}

Seller Profile Details:
{seller_profile_str if seller_profile_str else 'N/A'}
"""

            documents = [
                Document(text=ad_text, metadata={"doc_type": "ad_data"}),
                Document(text=f"Initial AI Analysis of the Ad:\n{initial_analysis_text}", metadata={"doc_type": "initial_analysis"})
            ]

            index = VectorStoreIndex.from_documents(documents)

            # System prompt for the chat engine
            system_prompt = (
                "You are a helpful AI assistant helping a user understand an online classified ad and its AI-generated analysis. "
                "Your goal is to answer questions about the ad or the analysis. "
                "Use the provided ad data and the initial AI analysis as your primary context. "
                "Be concise and informative. If the information is not in the documents, say you don't have that information."
            )

            chat_engine = index.as_chat_engine(
                chat_mode="context", # Uses context of documents for Q&A
                verbose=True,
                system_prompt=system_prompt,
            )
            logger.info("LlamaIndex Chat Engine erfolgreich erstellt.")
            return chat_engine
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der LlamaIndex Chat Engine: {str(e)}")
            return None # Or raise exception

    def chat_with_ad_context(self, question: str, chat_engine):
        """
        Führt ein Chat-Gespräch mit dem LlamaIndex Chat Engine.
        Ersetzt ask_followup_question.
        """
        from datetime import datetime # Local import for this method
        logger.info(f"Anfrage an LlamaIndex Chat Engine: {question}")
        if not chat_engine:
            logger.error("Chat Engine ist nicht initialisiert.")
            return {
                "success": False,
                "question": question,
                "error": "Chat engine not available.",
                "model": Settings.llm.model_name if Settings.llm else self.model_name,
                "asked_at": datetime.now().isoformat(),
            }
        try:
            response = chat_engine.chat(question)
            answer_text = str(response)

            # Chat history from LlamaIndex chat engine can be complex.
            # For simple context chat_mode, chat_engine.chat_history might provide it.
            # This part may need adjustment based on LlamaIndex version and specific needs for history persistence.
            current_chat_history = []
            if hasattr(chat_engine, 'chat_history') and chat_engine.chat_history:
                for msg in chat_engine.chat_history:
                    current_chat_history.append({"role": str(msg.role).lower(), "content": msg.content})

            return {
                "success": True,
                "question": question,
                "answer": answer_text,
                "model": Settings.llm.model_name if Settings.llm else self.model_name,
                "asked_at": datetime.now().isoformat()
                # "chat_history": current_chat_history # Removed as per review for context chat mode
            }
        except Exception as e:
            logger.error(f"Fehler während LlamaIndex Chat: {str(e)}")
            return {
                "success": False,
                "question": question,
                "error": str(e),
                "model": Settings.llm.model_name if Settings.llm else self.model_name,
                "asked_at": datetime.now().isoformat(),
            }

    # ask_followup_question method is now replaced by chat_with_ad_context
    # def ask_followup_question(self, question: str, ad_id: str) -> Dict[str, Any]:
    #    ... (alte Logik wird entfernt oder auskommentiert) ...


# Hilfsfunktionen (save_analysis_result, save_chat_history) bleiben vorerst bestehen.
# save_chat_history muss ggf. angepasst werden, wenn app.py die Chat-Historie von LlamaIndex verarbeitet.

def save_analysis_result(ad_id: str, analysis_result: Dict[str, Any], output_dir: str = "output") -> str:
    """
    Speichert das Analyseergebnis als JSON-Datei. (Beibehalten)
    """
    # ... (existing save_analysis_result logic remains unchanged) ...
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{ad_id}_analysis.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)

    logger.info(f"Analyseergebnis gespeichert: {filepath}")
    return filepath

def save_chat_history(ad_id: str, chat_result: Dict[str, Any], output_dir: str = "output") -> str:
    """
    Speichert den Chatverlauf als JSON-Datei. (Muss ggf. angepasst werden)
    """
    # ... (existing save_chat_history logic remains unchanged for now) ...
    # This function will likely need changes in app.py or here to correctly handle
    # the chat history format provided by chat_with_ad_context.
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{ad_id}_chat.json"
    filepath = os.path.join(output_dir, filename)

    # The structure of chat_result['chat_history'] from LlamaIndex might be different.
    # Assuming it's a list of {"role": ..., "content": ...} dictionaries for now.

    # Load existing chat data if file exists
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                chat_data = json.load(f)
            except json.JSONDecodeError:
                chat_data = {} # Start fresh if file is corrupted
    else:
        chat_data = {}

    # Update chat history
    # The new chat_result['chat_history'] should be the full history from LlamaIndex
    chat_data['chat_history'] = chat_result.get('chat_history', [])
    chat_data['ad_id'] = ad_id
    chat_data['model'] = chat_result.get('model', chat_data.get('model')) # Update model if changed
    chat_data['last_updated'] = chat_result.get('asked_at', datetime.now().isoformat())
    if 'created_at' not in chat_data:
        chat_data['created_at'] = chat_data['last_updated']

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Chatverlauf gespeichert: {filepath}")
    return filepath
