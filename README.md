# Kleinanzeigen Scraper

Ein Python-Tool zum Extrahieren aller Informationen von einer Kleinanzeigen-Anzeige, inklusive Bilder. Verfügbar als Kommandozeilen-Tool und als Webapp mit Benutzeroberfläche.

## Funktionen

- Extraktion aller Textinformationen (Titel, Preis, Beschreibung, Details, Standort, etc.)
- Download aller Bilder der Anzeige
- Extraktion detaillierter Verkäuferinformationen durch Besuch des Verkäuferprofils
- Speicherung der Daten in strukturierter Form (JSON)
- Speicherung der Bilder in einem separaten Ordner
- Webbasierte Benutzeroberfläche für einfache Bedienung
- KI-Analyse der Anzeigen mit dem Gemini-Modell von Google

## Installation

1. Stellen Sie sicher, dass Python 3.6 oder höher installiert ist
2. Klonen Sie dieses Repository
3. Installieren Sie die erforderlichen Abhängigkeiten:

```bash
pip install -r requirements.txt
```

## Verwendung

### Kommandozeilen-Tool

#### Einfache Verwendung

```bash
python kleinanzeigen_scraper.py https://www.kleinanzeigen.de/s-anzeige/beispiel-anzeige/123456789-123-456
```

#### Mit benutzerdefiniertem Ausgabeverzeichnis

```bash
python kleinanzeigen_scraper.py https://www.kleinanzeigen.de/s-anzeige/beispiel-anzeige/123456789-123-456 --output meine_anzeigen
```

### Webapp

Starten Sie die Webapp mit:

```bash
python app.py
```

Öffnen Sie dann in Ihrem Browser die Adresse `http://localhost:5000` und geben Sie die URL einer Kleinanzeigen-Anzeige ein.

## Ausgabe

Der Scraper erstellt folgende Ausgabe:

1. Ein JSON-File mit allen Textinformationen der Anzeige (benannt nach der Anzeigen-ID)
2. Einen Unterordner "images" mit allen Bildern der Anzeige

### Beispiel für die JSON-Ausgabe

```json
{
  "id": "123456789",
  "url": "https://www.kleinanzeigen.de/s-anzeige/beispiel-anzeige/123456789-123-456",
  "scraped_at": "2023-07-01T12:34:56.789012",
  "title": "Beispiel Anzeige",
  "price": "100.00",
  "description": "Dies ist eine Beispielbeschreibung...",
  "details": {
    "Marke": "Beispielmarke",
    "Zustand": "Gebraucht"
  },
  "location": {
    "address": "12345 Musterstadt",
    "zip_code": "12345",
    "city": "Musterstadt"
  },
  "seller": {
    "name": "Max Mustermann",
    "type": "Privater Nutzer",
    "member_since": "April 2020",
    "user_id": "12345678",
    "profile_url": "https://www.kleinanzeigen.de/s-bestandsliste.html?userId=12345678",
    "profile": {
      "user_type": "Privater Nutzer",
      "member_since": "April 2020",
      "response_time": "Antwortet in der Regel innerhalb von 24 Stunden",
      "followers_count": 5,
      "active_ads_count": 12
    }
  },
  "images": [
    {
      "filename": "123456789_1.jpg",
      "original_url": "https://img.kleinanzeigen.de/example1.jpg",
      "width": 800,
      "height": 600,
      "size_bytes": 102400
    },
    {
      "filename": "123456789_2.jpg",
      "original_url": "https://img.kleinanzeigen.de/example2.jpg",
      "width": 800,
      "height": 600,
      "size_bytes": 98304
    }
  ]
}
```

## KI-Analyse mit Gemini

Die Anwendung bietet eine KI-Analyse-Funktion, die das Gemini-Modell von Google verwendet, um Anzeigen zu analysieren und einen detaillierten Bericht zu erstellen. Der Bericht enthält:

- Zusammenfassung des Angebots
- Bewertung des Preis-Leistungs-Verhältnisses
- Einschätzung der Seriosität des Verkäufers
- Auffälligkeiten oder Warnzeichen
- Empfehlungen für potenzielle Käufer

### Einrichtung der KI-Analyse

1. Erstellen Sie eine `.env`-Datei im Hauptverzeichnis des Projekts (oder kopieren Sie `.env.example` zu `.env`)
2. Fügen Sie Ihren Gemini API-Schlüssel hinzu:
   ```
   GEMINI_API_KEY=Ihr_API_Schlüssel_hier
   ```
3. Sie können einen Gemini API-Schlüssel unter [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) erhalten

### Verwendung der KI-Analyse

1. Scrapen Sie eine Anzeige wie gewohnt
2. Klicken Sie auf der Ergebnisseite auf den "KI-Analyse"-Button
3. Starten Sie die Analyse und warten Sie auf das Ergebnis
4. Der Analysebericht wird angezeigt und kann heruntergeladen werden

## Hinweise

- Bitte beachten Sie die Nutzungsbedingungen von Kleinanzeigen.de
- Verwenden Sie dieses Tool verantwortungsvoll und respektieren Sie die Privatsphäre der Verkäufer
- Übermäßiges Scraping kann zu einer Blockierung Ihrer IP-Adresse führen
- Die KI-Analyse ist eine Einschätzung und keine Garantie für die Qualität oder Echtheit eines Angebots

## Lizenz

MIT
