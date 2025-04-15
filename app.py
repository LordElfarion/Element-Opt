# Inside backend/app.py
import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for # Keep session import
from dotenv import load_dotenv
import secrets

# --- Import your custom modules ---
# Make sure these point to the updated files
from scraper import scrape_store_data
from ai_handler import get_shopify_seo_ai, get_social_media_ai, detect_language

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='../frontend/static')

# --- Configure Flask Sessions (Still useful for flash messages, future features) ---
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
if not os.getenv('FLASK_SECRET_KEY'):
     print("WARNING: FLASK_SECRET_KEY not set in .env. Using temporary key.")

# --- AI Configuration Check ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY: print("WARNING: GEMINI_API_KEY environment variable not found.")

# === Page Routes ===

@app.route('/')
def index():
    """ Redirects to the Shopify SEO page by default. """
    return redirect(url_for('shopify_seo_page'))

@app.route('/shopify-seo')
def shopify_seo_page():
    """ Renders the Shopify SEO analysis page. """
    return render_template('shopify_seo.html') # References shopify_seo_tool/backend/templates/shopify_seo.html

@app.route('/social-media')
def social_media_page():
    """ Renders the Social Media content generation page. """
    return render_template('social_media.html') # References shopify_seo_tool/backend/templates/social_media.html

# === API Endpoints ===

@app.route('/analyze-shopify', methods=['POST'])
def analyze_shopify_api():
    """ Handles the Shopify SEO analysis request using the updated modules. """
    if not request.is_json: return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()
    store_url = data.get('url')
    language = data.get('language', 'en') # Default to English if not provided

    if not store_url or not store_url.startswith(('http://', 'https://')):
        return jsonify({"error": "Invalid or missing 'url' parameter"}), 400

    print(f"API: Received Shopify analysis request for URL: {store_url}, Language: {language}")
    # Call the updated scraper
    scraped_data = scrape_store_data(store_url)
    # The scraper now returns an error dictionary on failure or disallowed by robots.txt
    if not scraped_data or scraped_data.get("error"):
        error_msg = scraped_data.get("error", "Failed to scrape store data (Unknown Error).") if scraped_data else "Scraper returned None."
        print(f"API Error (Scraper): {error_msg}")
        # Return 500 for server-side errors, 400 might be suitable for disallowed robots.txt
        status_code = 400 if "robots.txt" in error_msg else 500
        return jsonify({"error": error_msg}), status_code

    # Call the updated AI handler which expects richer data and returns structured JSON/error dict
    ai_results = get_shopify_seo_ai(scraped_data, language)

    # This error check remains valid as the AI handler returns {"error": ...} on failure
    if not ai_results or ai_results.get("error"):
        error_msg = ai_results.get("error", "Unknown error getting AI suggestions") if ai_results else "AI handler returned None or empty."
        raw_snippet = ai_results.get("raw_response_snippet", "") if ai_results else "" # Get snippet if available
        print(f"API Error (AI Shopify): {error_msg}")
        if raw_snippet: print(f"Raw AI Response Snippet: {raw_snippet}")
        return jsonify({"error": error_msg}), 500

    # ai_results is now the dictionary parsed from the AI's JSON response
    return jsonify(ai_results)

@app.route('/generate-social', methods=['POST'])
def generate_social_api():
    """ Handles the Social Media content generation request using the updated AI handler. """
    if not request.is_json: return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()

    platform = data.get('platform')
    topic = data.get('topic') # Expecting topic/description from frontend
    keywords = data.get('keywords', '') # Optional keywords string
    language = data.get('language', 'en') # Default to English

    if not platform: return jsonify({"error": "Missing 'platform' parameter"}), 400
    if not topic: return jsonify({"error": "Missing 'topic' or description parameter"}), 400

    print(f"API: Received social generation request for Platform: {platform}, Topic: {topic[:50]}..., Lang: {language}")

    # Call the updated AI handler which returns structured JSON/error dict
    ai_results = get_social_media_ai(platform=platform, topic=topic, keywords=keywords, target_language=language)

    # This error check remains valid
    if not ai_results or ai_results.get("error"):
        error_msg = ai_results.get("error", "Unknown error getting AI suggestions") if ai_results else "AI handler returned None or empty."
        raw_snippet = ai_results.get("raw_response_snippet", "") if ai_results else ""
        print(f"API Error (AI Social): {error_msg}")
        if raw_snippet: print(f"Raw AI Response Snippet: {raw_snippet}")
        return jsonify({"error": error_msg}), 500

    # ai_results is now the dictionary parsed from the AI's JSON response
    return jsonify(ai_results)

if __name__ == '__main__':
    # Set debug=False for production environments
    # Use 0.0.0.0 to be accessible on the network, or 127.0.0.1 for local only.
    app.run(host='0.0.0.0', port=5001, debug=True) # Keep debug=True for development