#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kleinanzeigen Scraper Webapp

Eine Flask-Anwendung, die den Kleinanzeigen-Scraper mit einer Benutzeroberfläche versieht.
"""

import os
import json
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from kleinanzeigen_scraper import KleinanzeigenScraper

# Flask-App initialisieren
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kleinanzeigen-scraper-secret-key'
app.config['UPLOAD_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
Bootstrap(app)

# Jinja-Kontext-Prozessor für globale Variablen
@app.context_processor
def inject_now():
    return {'now': datetime.now}

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
