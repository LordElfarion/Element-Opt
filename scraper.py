# Inside backend/scraper.py
import requests
from bs4 import BeautifulSoup
import time
import random
import json
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

# --- User Agents ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'
]

# --- Robots.txt Parser ---
def can_fetch(url, user_agent):
    """Checks robots.txt to see if the user agent is allowed to fetch the URL."""
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        print(f"Warning: Could not read or parse robots.txt at {robots_url}: {e}")
        return True # Be optimistic if robots.txt fails

# --- Scraper Function ---
def scrape_store_data(url):
    """
    Scrapes enhanced data from a store URL with basic politeness checks.
    """
    print(f"--- Starting scrape for: {url} ---")
    selected_user_agent = random.choice(USER_AGENTS)
    headers = {'User-Agent': selected_user_agent}

    # 1. Check robots.txt
    if not can_fetch(url, selected_user_agent):
        print(f"Error: Scraping disallowed by robots.txt for user agent {selected_user_agent}")
        return {"error": "Scraping disallowed by robots.txt"}

    try:
        time.sleep(random.uniform(1.0, 2.5)) # Increased random delay
        response = requests.get(url, headers=headers, timeout=20) # Increased timeout
        response.raise_for_status() # Check for HTTP errors (4xx, 5xx)

        if 'text/html' not in response.headers.get('Content-Type', '').lower():
             print(f"Warning: Content-Type is not HTML ({response.headers.get('Content-Type')})")
             # Allow processing anyway, but be aware it might fail
             # return {"error": f"Content-Type is not HTML ({response.headers.get('Content-Type')})"}

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Extract Core Data ---
        title = soup.title.string.strip() if soup.title else "No Title Found"

        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc_tag['content'].strip() if meta_desc_tag and meta_desc_tag.get('content') else "No Meta Description Found"

        h1_tag = soup.find('h1')
        h1_text = h1_tag.get_text(strip=True) if h1_tag else "No H1 Found"

        # --- Extract Headings ---
        headings = {}
        for i in range(1, 7):
            heading_tags = soup.find_all(f'h{i}')
            if heading_tags:
                headings[f'h{i}'] = [h.get_text(strip=True) for h in heading_tags]

        # --- Extract Image Alt Text ---
        alt_texts = []
        images = soup.find_all('img', limit=10) # Limit to first 10 images
        for img in images:
            alt = img.get('alt', '').strip()
            if alt: # Only include non-empty alt texts
                alt_texts.append(alt)
            # else: # Optionally track images missing alt text
            #    alt_texts.append("Missing Alt Text")

        # --- Extract Schema.org JSON-LD ---
        schema_data = []
        schema_scripts = soup.find_all('script', type='application/ld+json')
        for script in schema_scripts:
            try:
                schema_json = json.loads(script.string)
                schema_data.append(schema_json)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Could not parse JSON-LD script: {e}")
                print(f"Script content: {script.string[:100]}...") # Log snippet
            except Exception as e:
                 print(f"Warning: Unexpected error parsing JSON-LD script: {e}")


        # --- Extract Links ---
        internal_links = 0
        external_links = 0
        base_domain = urlparse(url).netloc
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            parsed_href = urlparse(urljoin(url, href)) # Handle relative URLs
            if parsed_href.netloc == base_domain:
                internal_links += 1
            elif parsed_href.scheme in ['http', 'https']: # Basic check for external http(s) links
                external_links += 1

        # --- Extract Content Snippet (Improved) ---
        content_source = None
        selectors = ['main', 'article', 'div[role="main"]', 'body'] # Try common content containers
        for selector in selectors:
            content_source = soup.select_one(selector)
            if content_source:
                break

        body_text = ""
        if content_source:
             # Extract text more broadly within the chosen container
             # Join text nodes directly, then clean up whitespace
             all_text = content_source.find_all(string=True)
             body_text = ' '.join(t.strip() for t in all_text if t.parent.name not in ['script', 'style', 'head', 'title', 'meta', '[document]'] and t.strip())
        else:
             body_text = "Could not identify main content area."

        max_length = 5000 # Increased max length
        content_snippet = ' '.join(body_text.split())[:max_length] # Clean whitespace and truncate

        print("--- Scraping successful (enhanced data extracted) ---")
        return {
            "url": url,
            "title": title,
            "meta_description": description,
            "h1": h1_text,
            "headings": headings, # Dict of lists h1-h6
            "alt_texts": alt_texts, # List of strings
            "schema_data": schema_data, # List of dicts
            "links": {"internal": internal_links, "external": external_links}, # Dict
            "content_snippet": content_snippet # String
        }
    except requests.exceptions.Timeout:
         print(f"Error: Timeout scraping {url}")
         return {"error": f"Timeout scraping {url}"}
    except requests.exceptions.HTTPError as e:
         print(f"Error: HTTP Error {e.response.status_code} for {url}")
         return {"error": f"HTTP Error {e.response.status_code} for {url}"}
    except requests.exceptions.ConnectionError:
        print(f"Error: Connection error for {url}")
        return {"error": f"Connection error for {url}"}
    except requests.exceptions.RequestException as e:
        print(f"Error: General request error scraping {url}: {e}")
        return {"error": f"Request error: {e}"}
    except AttributeError as e:
         print(f"Error: Could not parse HTML structure (AttributeError): {e}. Page structure might be unexpected.")
         return {"error": f"HTML parsing error (AttributeError): {e}"}
    except Exception as e:
        print(f"An unexpected error occurred during scraping: {e}")
        return {"error": f"An unexpected error occurred: {e}"}