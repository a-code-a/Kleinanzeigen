#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Setze die Standardkodierung auf UTF-8
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

"""
Kleinanzeigen Scraper

Dieses Skript extrahiert alle Informationen von einer Kleinanzeigen-Anzeige,
inklusive Bilder, und speichert diese strukturiert ab.
"""

import os
import re
import json
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from PIL import Image
from io import BytesIO

class KleinanzeigenScraper:
    """Scraper für Kleinanzeigen.de"""

    def __init__(self, output_dir="output"):
        """
        Initialisiert den Scraper.

        Args:
            output_dir (str): Verzeichnis für die Ausgabe der Daten
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")

        # Erstelle Ausgabeverzeichnisse, falls sie nicht existieren
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

    def scrape(self, url):
        """
        Scrapt eine Kleinanzeigen-Anzeige.

        Args:
            url (str): URL der Kleinanzeigen-Anzeige

        Returns:
            dict: Extrahierte Daten der Anzeige
        """
        print(f"Scrape Anzeige: {url}")

        # Anzeigen-ID aus URL extrahieren
        ad_id = self._extract_ad_id(url)
        if not ad_id:
            raise ValueError(f"Konnte keine Anzeigen-ID aus der URL extrahieren: {url}")

        # Seite abrufen
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Fehler beim Abrufen der Seite: HTTP {response.status_code}")

        # Erzwinge UTF-8-Kodierung
        response.encoding = 'utf-8'

        # HTML parsen
        soup = BeautifulSoup(response.text, 'html.parser')

        # Daten extrahieren
        data = {
            "id": ad_id,
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "title": self._extract_title(soup),
            "price": self._extract_price(soup),
            "description": self._extract_description(soup),
            "details": self._extract_details(soup),
            "location": self._extract_location(soup),
            "seller": self._extract_seller_info(soup),
            "images": self._extract_and_save_images(soup, ad_id)
        }

        # Daten speichern
        self._save_data(data, ad_id)

        return data

    def _extract_ad_id(self, url):
        """Extrahiert die Anzeigen-ID aus der URL"""
        match = re.search(r'/(\d+)-', url)
        return match.group(1) if match else None

    def _extract_title(self, soup):
        """Extrahiert den Titel der Anzeige"""
        title_elem = soup.select_one('h1.boxedarticle--title')
        return title_elem.text.strip() if title_elem else None

    def _extract_price(self, soup):
        """Extrahiert den Preis der Anzeige"""
        price_elem = soup.select_one('h2.boxedarticle--price')
        if not price_elem:
            return None

        price_text = price_elem.text.strip()
        # Preis bereinigen (z.B. "80 € VB" -> "80")
        price_match = re.search(r'(\d+(?:\.\d+)?)', price_text.replace(',', '.'))
        return price_match.group(1) if price_match else price_text

    def _extract_description(self, soup):
        """Extrahiert die Beschreibung der Anzeige"""
        desc_elem = soup.select_one('p#viewad-description-text')
        return desc_elem.text.strip() if desc_elem else None

    def _extract_details(self, soup):
        """Extrahiert die Details der Anzeige"""
        details = {}

        # Suche nach der addetailslist
        addetailslist = soup.select_one('div.addetailslist')
        if not addetailslist:
            return details

        # Extrahiere alle Detail-Elemente
        detail_items = addetailslist.select('li.addetailslist--detail')

        for item in detail_items:
            # Extrahiere den Label-Text (alles vor dem ersten span)
            label_text = None
            value_text = None

            # Direkter Zugriff auf den Text vor dem span
            for content in item.contents:
                if content.name != 'span':
                    if content.string and content.string.strip():
                        label_text = content.string.strip()
                        if label_text.endswith(':'):
                            label_text = label_text[:-1].strip()
                        break

            # Extrahiere den Wert aus dem span
            value_elem = item.select_one('.addetailslist--detail--value')
            if value_elem:
                value_text = value_elem.text.strip()

            if label_text and value_text:
                details[label_text] = value_text

        return details

    def _extract_location(self, soup):
        """Extrahiert den Standort der Anzeige"""
        location = {}

        location_elem = soup.select_one('span#viewad-locality')
        if location_elem:
            location['address'] = location_elem.text.strip()

        # Versuche, PLZ und Ort zu extrahieren
        if 'address' in location:
            match = re.search(r'(\d{5})\s+(.+)', location['address'])
            if match:
                location['zip_code'] = match.group(1)
                location['city'] = match.group(2)

        return location

    def _extract_seller_info(self, soup):
        """Extrahiert Informationen zum Verkäufer"""
        seller = {}

        # Verkäufername
        seller_name_elem = soup.select_one('.userprofile-vip')
        if seller_name_elem:
            seller['name'] = seller_name_elem.text.strip()

        # Verkäufertyp (privat/gewerblich)
        seller_type_elem = soup.select_one('.userprofile-vip-details-text')
        if seller_type_elem:
            seller['type'] = seller_type_elem.text.strip()

        # Mitglied seit
        member_since_elems = soup.select('.userprofile-vip-details-text')
        for elem in member_since_elems:
            if 'Aktiv seit' in elem.text:
                seller['member_since'] = elem.text.replace('Aktiv seit', '').strip()
                break

        # Verkäufer-ID und Profillink extrahieren
        seller_profile_link = soup.select_one('a[href*="/s-bestandsliste.html?userId="]')
        if seller_profile_link:
            profile_url = seller_profile_link.get('href')
            # Extrahiere die User-ID aus der URL
            user_id_match = re.search(r'userId=(\d+)', profile_url)
            if user_id_match:
                user_id = user_id_match.group(1)
                seller['user_id'] = user_id

                # Vollständige URL zum Profil erstellen
                full_profile_url = urljoin('https://www.kleinanzeigen.de', profile_url)
                seller['profile_url'] = full_profile_url

                # Profilseite des Verkäufers scrapen
                print(f"Scrape Verkäuferprofil: {full_profile_url}")
                seller_profile_data = self._scrape_seller_profile(full_profile_url)

                # Profilinformationen zum Verkäufer hinzufügen
                if seller_profile_data:
                    seller.update(seller_profile_data)

        return seller

    def _scrape_seller_profile(self, profile_url):
        """
        Scrapt die Profilseite eines Verkäufers.

        Args:
            profile_url (str): URL der Profilseite

        Returns:
            dict: Extrahierte Profilinformationen
        """
        try:
            # Profilseite abrufen
            response = requests.get(profile_url, headers=self.headers)
            if response.status_code != 200:
                print(f"Fehler beim Abrufen der Profilseite: HTTP {response.status_code}")
                return {}

            # Erzwinge UTF-8-Kodierung
            response.encoding = 'utf-8'

            # HTML parsen
            soup = BeautifulSoup(response.text, 'html.parser')

            # Profilinformationen extrahieren
            profile_data = {
                'profile': {}
            }

            # Profilinformationen aus den userprofile-details Elementen extrahieren
            profile_info_elems = soup.select('.userprofile-details')
            for elem in profile_info_elems:
                details_text = elem.select_one('.userprofile-details-text')

                if details_text:
                    details_text = details_text.text.strip()

                    # Nutzertyp (Privat/Gewerblich)
                    if 'Privater Nutzer' in details_text or 'Gewerblicher Nutzer' in details_text:
                        profile_data['profile']['user_type'] = details_text

                    # Aktiv seit
                    elif 'Aktiv seit' in details_text:
                        profile_data['profile']['member_since'] = details_text.replace('Aktiv seit', '').strip()

                    # Antwortzeit
                    elif 'Antwortet in der Regel innerhalb von' in details_text:
                        profile_data['profile']['response_time'] = details_text

                    # Follower
                    elif 'Follower' in details_text:
                        follower_match = re.search(r'(\d+)', details_text)
                        if follower_match:
                            profile_data['profile']['followers_count'] = int(follower_match.group(1))

                    # Adresse/Ort (falls vorhanden)
                    elif 'Adresse:' in details_text:
                        address = details_text.replace('Adresse:', '').strip()
                        profile_data['profile']['address'] = address

                    # Telefonnummer (falls öffentlich)
                    elif 'Telefon:' in details_text:
                        phone = details_text.replace('Telefon:', '').strip()
                        profile_data['profile']['phone'] = phone

            # Anzahl der aktiven Anzeigen aus dem Seitentitel extrahieren
            title_elem = soup.select_one('title')
            if title_elem:
                title_text = title_elem.text.strip()
                # Extrahiere die Anzahl der Anzeigen aus dem Titel, falls vorhanden
                ads_count_match = re.search(r'(\d+)\s+Anzeigen', title_text)
                if ads_count_match:
                    profile_data['profile']['active_ads_count'] = int(ads_count_match.group(1))
                else:
                    # Wenn keine Anzahl im Titel, dann hat der Nutzer wahrscheinlich nur eine Anzeige
                    profile_data['profile']['active_ads_count'] = 1

            # Bewertungen (falls vorhanden)
            rating_elem = soup.select_one('.userbadges--rating')
            if rating_elem:
                rating_text = rating_elem.text.strip()
                rating_match = re.search(r'(\d+)\s*%', rating_text)
                if rating_match:
                    profile_data['profile']['rating_percentage'] = int(rating_match.group(1))

                # Anzahl der Bewertungen
                reviews_count_elem = soup.select_one('.userbadges--rating-count')
                if reviews_count_elem:
                    reviews_count_text = reviews_count_elem.text.strip()
                    reviews_count_match = re.search(r'(\d+)', reviews_count_text)
                    if reviews_count_match:
                        profile_data['profile']['reviews_count'] = int(reviews_count_match.group(1))

            return profile_data

        except Exception as e:
            print(f"Fehler beim Scrapen des Verkäuferprofils: {str(e)}")
            return {}

    def _extract_and_save_images(self, soup, ad_id):
        """Extrahiert und speichert Bilder der Anzeige"""
        images_info = []

        # Bildergalerie finden
        gallery_items = soup.select('div.galleryimage-element img')

        for i, img in enumerate(gallery_items):
            # Bild-URL extrahieren (normalerweise im data-imgsrc Attribut für hochauflösende Bilder)
            img_url = img.get('data-imgsrc') or img.get('src')
            if not img_url:
                continue

            # Relative URLs in absolute URLs umwandeln
            if not img_url.startswith(('http://', 'https://')):
                img_url = urljoin('https://www.kleinanzeigen.de', img_url)

            try:
                # Bild herunterladen
                img_response = requests.get(img_url, headers=self.headers)
                if img_response.status_code != 200:
                    print(f"Fehler beim Herunterladen des Bildes {img_url}: HTTP {img_response.status_code}")
                    continue

                # Dateiname generieren
                file_ext = self._get_image_extension(img_response.headers.get('Content-Type', ''))
                filename = f"{ad_id}_{i+1}{file_ext}"
                filepath = os.path.join(self.images_dir, filename)

                # Bild speichern
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)

                # Bildgröße ermitteln
                img_data = BytesIO(img_response.content)
                with Image.open(img_data) as img_obj:
                    width, height = img_obj.size

                # Bildinformationen speichern
                images_info.append({
                    'filename': filename,
                    'original_url': img_url,
                    'width': width,
                    'height': height,
                    'size_bytes': len(img_response.content)
                })

                print(f"Bild gespeichert: {filename}")

            except Exception as e:
                print(f"Fehler beim Verarbeiten des Bildes {img_url}: {str(e)}")

        return images_info

    def _get_image_extension(self, content_type):
        """Ermittelt die Dateierweiterung basierend auf dem Content-Type"""
        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'
        elif 'webp' in content_type:
            return '.webp'
        else:
            return '.jpg'  # Standardwert

    def _save_data(self, data, ad_id):
        """Speichert die extrahierten Daten als JSON"""
        filename = f"{ad_id}.json"
        filepath = os.path.join(self.output_dir, filename)

        # Korrigiere Zeichenkodierung in Details
        if 'details' in data:
            corrected_details = {}
            for key, value in data['details'].items():
                # Entferne Zeilenumbrüche und überflüssige Leerzeichen im Schlüssel
                clean_key = key.replace('\n', '').strip()
                corrected_details[clean_key] = value
            data['details'] = corrected_details

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Daten gespeichert: {filepath}")


def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(description='Kleinanzeigen Scraper')
    parser.add_argument('url', help='URL der Kleinanzeigen-Anzeige')
    parser.add_argument('--output', '-o', default='output', help='Ausgabeverzeichnis')
    args = parser.parse_args()

    scraper = KleinanzeigenScraper(output_dir=args.output)
    try:
        scraper.scrape(args.url)
        print(f"Scraping erfolgreich abgeschlossen. Daten wurden in '{args.output}' gespeichert.")
    except Exception as e:
        print(f"Fehler beim Scrapen: {str(e)}")


if __name__ == "__main__":
    main()
