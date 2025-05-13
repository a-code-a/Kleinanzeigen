#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kleinanzeigen Scraper Webapp

Eine Flask-Anwendung, die den Kleinanzeigen-Scraper mit einer Benutzeroberfläche versieht.
"""

import os
import json
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, flash
from flask_bootstrap import Bootstrap
from kleinanzeigen_scraper import KleinanzeigenScraper
from gemini_analyzer import GeminiAnalyzer, save_analysis_result, save_chat_history

# Umgebungsvariablen aus .env-Datei laden
load_dotenv()

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask-App initialisieren
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'kleinanzeigen-scraper-secret-key')
app.config['UPLOAD_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')  # Gemini API-Schlüssel aus Umgebungsvariable
Bootstrap(app)

# Überprüfen, ob der API-Schlüssel gesetzt ist
if not app.config['GEMINI_API_KEY']:
    logger.warning("GEMINI_API_KEY ist nicht gesetzt. Die KI-Analyse-Funktion wird nicht verfügbar sein.")
    app.config['GEMINI_AVAILABLE'] = False
else:
    app.config['GEMINI_AVAILABLE'] = True

# Jinja-Kontext-Prozessor für globale Variablen
@app.context_processor
def inject_globals():
    return {
        'now': datetime.now,
        'gemini_available': app.config.get('GEMINI_AVAILABLE', False)
    }

# Markdown-Filter für Jinja2
@app.template_filter('markdown')
def markdown_filter(text):
    """Konvertiert Markdown-Text in HTML"""
    try:
        import markdown
        # Wenn der Text bereits HTML-Tags enthält, geben wir ihn unverändert zurück
        if '<p>' in text or '<ul>' in text or '<li>' in text:
            return text
        # Ansonsten konvertieren wir Markdown zu HTML
        return markdown.markdown(text, extensions=['extra', 'nl2br', 'sane_lists'])
    except ImportError:
        # Fallback, wenn markdown nicht installiert ist
        if '<p>' in text or '<ul>' in text or '<li>' in text:
            return text
        return text.replace('\n', '<br>')

# Stellen Sie sicher, dass die Ausgabeverzeichnisse existieren
os.makedirs('output', exist_ok=True)
os.makedirs('output/images', exist_ok=True)

def is_valid_kleinanzeigen_url(url):
    """Überprüft, ob die URL eine gültige Kleinanzeigen-URL ist"""
    pattern = r'^https?://(?:www\.)?kleinanzeigen\.de/s-anzeige/.+/\d+-\d+-\d+$'
    return re.match(pattern, url) is not None

@app.route('/')
def index():
    """Startseite mit URL-Eingabeformular"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Verarbeitet die Anfrage zum Scrapen einer URL"""
    url = request.form.get('url', '').strip()

    # URL validieren
    if not url:
        return render_template('index.html', error='Bitte geben Sie eine URL ein.')

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    if not is_valid_kleinanzeigen_url(url):
        return render_template('index.html', error='Bitte geben Sie eine gültige Kleinanzeigen-URL ein.')

    try:
        # Scraper initialisieren und URL scrapen
        scraper = KleinanzeigenScraper(output_dir='output')
        data = scraper.scrape(url)

        # Zur Ergebnisseite weiterleiten
        ad_id = data['id']
        return redirect(url_for('result', ad_id=ad_id))

    except Exception as e:
        return render_template('index.html', error=f'Fehler beim Scrapen: {str(e)}')

@app.route('/result/<ad_id>')
def result(ad_id):
    """Zeigt die Ergebnisse für eine bestimmte Anzeigen-ID an"""
    try:
        # JSON-Datei lesen
        json_path = os.path.join('output', f'{ad_id}.json')
        if not os.path.exists(json_path):
            return render_template('index.html', error=f'Keine Daten für Anzeigen-ID {ad_id} gefunden.')

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return render_template('result.html', data=data)

    except Exception as e:
        return render_template('index.html', error=f'Fehler beim Laden der Ergebnisse: {str(e)}')

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Stellt Bilder aus dem Ausgabeverzeichnis bereit"""
    return send_from_directory('output/images', filename)

@app.route('/download/<ad_id>')
def download_json(ad_id):
    """Ermöglicht den Download der JSON-Datei"""
    return send_from_directory('output', f'{ad_id}.json', as_attachment=True)

@app.route('/analyze/<ad_id>', methods=['GET', 'POST'])
def analyze(ad_id):
    """Analysiert eine Anzeige mit dem Gemini-Modell und ermöglicht Folgefragen"""
    # Überprüfen, ob die Gemini API verfügbar ist
    if not app.config.get('GEMINI_AVAILABLE', False):
        flash('Die KI-Analyse-Funktion ist nicht verfügbar. Bitte stellen Sie sicher, dass der GEMINI_API_KEY in der .env-Datei gesetzt ist.', 'warning')
        return redirect(url_for('result', ad_id=ad_id))

    try:
        # JSON-Datei lesen
        json_path = os.path.join('output', f'{ad_id}.json')
        if not os.path.exists(json_path):
            flash('Keine Daten für Anzeigen-ID gefunden.', 'danger')
            return redirect(url_for('index'))

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Prüfen, ob bereits eine Analyse existiert
        analysis_path = os.path.join('output', f'{ad_id}_analysis.json')
        analysis_exists = os.path.exists(analysis_path)

        # Prüfen, ob bereits ein Chat existiert
        chat_path = os.path.join('output', f'{ad_id}_chat.json')
        chat_data = None
        if os.path.exists(chat_path):
            with open(chat_path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)

        # Wenn POST-Anfrage mit Frage, dann Folgefrage stellen
        if request.method == 'POST' and 'question' in request.form and analysis_exists:
            question = request.form.get('question', '').strip()

            if not question:
                flash('Bitte geben Sie eine Frage ein.', 'warning')
                return redirect(url_for('analyze', ad_id=ad_id))

            # Analyse-Daten laden
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)

            # Gemini Analyzer initialisieren
            analyzer = GeminiAnalyzer(api_key=app.config['GEMINI_API_KEY'])

            # Chatverlauf laden, falls vorhanden
            if chat_data and 'chat_history' in chat_data:
                analyzer.chat_history = chat_data['chat_history']
            elif analysis_data and 'chat_history' in analysis_data:
                analyzer.chat_history = analysis_data['chat_history']

            # Folgefrage stellen
            chat_result = analyzer.ask_followup_question(question, ad_id)

            # Chatverlauf speichern
            save_chat_history(ad_id, chat_result)

            # Chat-Daten aktualisieren
            with open(chat_path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)

            return render_template('analysis.html', data=data, analysis=analysis_data, chat=chat_data)

        # Wenn POST-Anfrage ohne Frage, dann Analyse durchführen
        elif request.method == 'POST' and not analysis_exists:
            # Bilder für die Analyse sammeln
            image_paths = []
            for image in data.get('images', []):
                if 'filename' in image:
                    image_path = os.path.join('output', 'images', image['filename'])
                    if os.path.exists(image_path):
                        image_paths.append(image_path)

            # Gemini Analyzer initialisieren und Analyse durchführen
            analyzer = GeminiAnalyzer(api_key=app.config['GEMINI_API_KEY'])
            analysis_result = analyzer.analyze(data, image_paths)

            # Analyseergebnis speichern
            save_analysis_result(ad_id, analysis_result)

            return render_template('analysis.html', data=data, analysis=analysis_result, chat=None)

        # Bei GET-Anfrage und existierender Analyse, Analyse anzeigen
        elif analysis_exists:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            return render_template('analysis.html', data=data, analysis=analysis_data, chat=chat_data)

        # Bei GET-Anfrage ohne existierende Analyse, Formular anzeigen
        else:
            return render_template('analyze_form.html', data=data)

    except Exception as e:
        logger.error(f"Fehler bei der Analyse: {str(e)}")
        flash(f'Fehler bei der Analyse: {str(e)}', 'danger')
        return redirect(url_for('result', ad_id=ad_id))

@app.route('/download_analysis/<ad_id>')
def download_analysis(ad_id):
    """Ermöglicht den Download der Analysedatei"""
    return send_from_directory('output', f'{ad_id}_analysis.json', as_attachment=True)

@app.route('/download_chat/<ad_id>')
def download_chat(ad_id):
    """Ermöglicht den Download des Chatverlaufs"""
    return send_from_directory('output', f'{ad_id}_chat.json', as_attachment=True)

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API-Endpunkt zum Scrapen einer URL"""
    data = request.get_json()
    url = data.get('url', '').strip() if data else ''

    if not url:
        return jsonify({'error': 'Keine URL angegeben'}), 400

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    if not is_valid_kleinanzeigen_url(url):
        return jsonify({'error': 'Ungültige Kleinanzeigen-URL'}), 400

    try:
        # Scraper initialisieren und URL scrapen
        scraper = KleinanzeigenScraper(output_dir='output')
        result_data = scraper.scrape(url)

        return jsonify({'success': True, 'data': result_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
