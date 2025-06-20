# Kleinanzeigen Scraper

A Python tool for extracting all information from a Kleinanzeigen ad, including images. Available as a command-line tool and as a web app with a user interface. The web app now features automatic AI-powered analysis of ads and an interactive chat to discuss the ad's details, leveraging Google's Gemini model and LlamaIndex for contextual understanding.

## Project Structure

This project is organized as follows:

-   \`app.py\`: The main Flask web application that provides the user interface and handles web requests.
-   \`kleinanzeigen_scraper.py\`: Contains the core logic for scraping ad data from Kleinanzeigen.de. It can also be run as a command-line tool.
-   \`gemini_analyzer.py\`: Implements the AI analysis features using Google's Gemini model to analyze scraped ad data, and integrates LlamaIndex for chat functionality.
-   \`templates/\`: Directory containing HTML templates used by the Flask web application.
-   \`static/\`: Directory for static files like CSS stylesheets and JavaScript client-side scripts.
-   \`output/\`: Default directory where scraped ad data (JSON files) and downloaded images are saved.
-   \`requirements.txt\`: Lists all Python dependencies required for this project.
-   \`.env.example\`: An example file showing the environment variables that can be configured, primarily for the `GEMINI_API_KEY`.
-   \`README.md\`: This file, providing information about the project.

## Features

- Extraction of all text information (title, price, description, details, location, etc.)
- Download of all images from the ad
- Extraction of detailed seller information by visiting the seller's profile
- Storage of data in structured form (JSON)
- Storage of images in a separate folder
- Web-based user interface for easy operation
- Automatic AI analysis of ads upon scraping, providing an immediate summary and evaluation using Google's Gemini model.
- Interactive chat with the AI about the ad, using the ad's details and initial analysis as context, powered by LlamaIndex.

## Installation

1. Ensure that Python 3.6 or higher is installed
2. Clone this repository
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   3. Create a `.env` file for your environment variables. You can copy the example file:
      ```bash
      cp .env.example .env
      ```
      Then, edit the `.env` file to add your `GEMINI_API_KEY` if you plan to use the AI analysis features. You can also set a custom `FLASK_SECRET_KEY` for the web application.
4. The application will attempt to create an `output/` directory for scraped data and images if it doesn't exist. You can also create it manually.

## Usage

### Command-line Tool

#### Simple Usage

```bash
python kleinanzeigen_scraper.py https://www.kleinanzeigen.de/s-anzeige/beispiel-anzeige/123456789-123-456
```

#### With custom output directory

```bash
python kleinanzeigen_scraper.py https://www.kleinanzeigen.de/s-anzeige/beispiel-anzeige/123456789-123-456 --output my_ads
```

### Web app

Start the web app with:

```bash
python app.py
```

Then open the address `http://localhost:5000` in your browser, enter a Kleinanzeigen ad URL, and submit. The results page will display the scraped ad details, an automatically generated AI analysis, and an interactive chat interface to ask further questions about the ad.

## Output

The scraper creates the following output:

1. A JSON file with all text information of the ad (named after the ad ID)
2. A subfolder "images" with all images of the ad
3. If AI features are enabled, an additional JSON file (`<ad_id>_analysis.json`) containing the initial AI analysis.

### Example of JSON output

(The existing example for the main ad data JSON remains relevant)
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
    "active_ads_count": 12,
    "badges": ["TOP Zufriedenheit", "Sehr freundlich"],
    "profile": {
      "user_type": "Privater Nutzer",
      "member_since": "April 2020",
      "response_time": "Antwortet in der Regel innerhalb von 24 Stunden",
      "followers_count": 5,
      "active_ads_count": 12,
      "rating_percentage": 95,
      "reviews_count": 25,
      "badges": ["Zuverlässig"]
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

## AI Analysis and Chat with Gemini & LlamaIndex

The application automatically performs an AI analysis using Google's Gemini model when an ad is scraped via the web interface. This initial analysis provides a quick overview, including:

- Summary of the offer
- Evaluation of the price-performance ratio
- Assessment of the seller's seriousness
- Abnormalities or warning signs
- Recommendations for potential buyers

Furthermore, the results page features an interactive chat. This chat functionality leverages LlamaIndex to provide context-aware responses based on the scraped ad data and the initial AI analysis.

### Setup of AI Analysis

To use the AI analysis and chat features:

1.  **Ensure you have a Gemini API Key.** You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  **Set up your environment file:**
    *   If you haven't already, copy the `.env.example` file to a new file named `.env` in the project's root directory:
        ```bash
        cp .env.example .env
        ```
    *   Open the `.env` file and add your Gemini API key:
        ```
        GEMINI_API_KEY=your_api_key_here
        ```
3.  **Verify API Key Access:** The application checks for the `GEMINI_API_KEY` on startup. If it's not set, AI features will be disabled (a warning will be logged, and the UI may indicate this).

The `FLASK_SECRET_KEY` for the web application can also be set in this `.env` file. While not strictly for AI analysis, it's good practice for web app security.

### Interacting with AI Analysis and Chat

1.  **Scrape an ad** using the web app's main page by entering its URL.
2.  The **results page will automatically display** the scraped details alongside an initial AI-generated analysis of the ad.
3.  **Use the chat interface** provided on the results page to ask follow-up questions. The AI uses the ad's content and its initial analysis to answer your questions contextually.

## Notices

- Please note the terms of use of Kleinanzeigen.de
- Use this tool responsibly and respect the privacy of sellers
- Excessive scraping can lead to your IP address being blocked
- The AI analysis and chat responses are assessments and not guarantees for the quality or authenticity of an offer.

## License

MIT
