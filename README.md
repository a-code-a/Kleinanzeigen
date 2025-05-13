# Kleinanzeigen Scraper

Ein Python-Tool zum Extrahieren aller Informationen von einer Kleinanzeigen-Anzeige, inklusive Bilder.

## Funktionen

- Extraktion aller Textinformationen (Titel, Preis, Beschreibung, Details, Standort, etc.)
- Download aller Bilder der Anzeige
- Extraktion detaillierter Verkäuferinformationen durch Besuch des Verkäuferprofils
- Speicherung der Daten in strukturierter Form (JSON)
- Speicherung der Bilder in einem separaten Ordner

## Installation

1. Stellen Sie sicher, dass Python 3.6 oder höher installiert ist
2. Klonen Sie dieses Repository
3. Installieren Sie die erforderlichen Abhängigkeiten:

```bash
pip install -r requirements.txt
```

## Verwendung

### Einfache Verwendung

```bash
python kleinanzeigen_scraper.py https://www.kleinanzeigen.de/s-anzeige/beispiel-anzeige/123456789-123-456
```

### Mit benutzerdefiniertem Ausgabeverzeichnis

```bash
python kleinanzeigen_scraper.py https://www.kleinanzeigen.de/s-anzeige/beispiel-anzeige/123456789-123-456 --output meine_anzeigen
```

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

## Hinweise

- Bitte beachten Sie die Nutzungsbedingungen von Kleinanzeigen.de
- Verwenden Sie dieses Tool verantwortungsvoll und respektieren Sie die Privatsphäre der Verkäufer
- Übermäßiges Scraping kann zu einer Blockierung Ihrer IP-Adresse führen

## Lizenz

MIT
