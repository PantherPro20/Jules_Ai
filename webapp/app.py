from flask import Flask, jsonify, render_template, request, session
import json
import os
import datetime
import pytz # For timezone handling
import re # For simple tokenization and keyword extraction
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This should be one of the first things done in the script
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24) # Or a fixed secret string for development

# --- Configuration for APIs ---
# IMPORTANT: Store these securely, e.g., in environment variables
# For local development, you might set them directly here for testing,
# but they should NOT be hardcoded in production code committed to a repo.
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GOOGLE_CSE_ID = os.environ.get('GOOGLE_CSE_ID', '63bdfe80d8bfe4a62') # Defaulting to user-provided CSE ID

# Basic check if keys are loaded (optional, for early warning)
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY environment variable not set.")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable not set.")
if not GOOGLE_CSE_ID: # Check if it was loaded from env or is using default
    print("Warning: GOOGLE_CSE_ID environment variable not set, using default or placeholder.")

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    app.logger.warning("GEMINI_API_KEY not set. Summarization will not be available.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_FILE = os.path.join(BASE_DIR, "../data/scraped_data.json") # No longer needed

# Basic list of English stop words
STOP_WORDS = set([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", # noqa (keep for now)
    "have", "has", "had", "do", "does", "did", "will", "would", "should",
    "can", "could", "may", "might", "must", "about", "above", "after",
    "again", "against", "all", "am", "and", "any", "as", "at", "because",
    "before", "below", "between", "both", "but", "by", "com", "for", "from",
    "further", "here", "how", "if", "in", "into", "it", "its", "itself",
    "let", "me", "more", "most", "my", "myself", "nor", "of", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "so", "some", "such", "than", "that", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "what",
    "when", "where", "which", "while", "who", "whom", "why", "with", "www",
    "information", "latest", "news", "articles", "find", "show", "tell", "me"
])

# Known sources for filtering
KNOWN_SOURCES = {
    "bbc": "BBC News",
    "cnn": "CNN News",
    "wikipedia": "Wikipedia"
}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/time')
def get_time():
    timezone_str = request.args.get('tz', default='UTC', type=str)
    try:
        user_timezone = pytz.timezone(timezone_str)
        current_time = datetime.datetime.now(user_timezone)
        return jsonify({
            "time": current_time.strftime('%H:%M:%S'),
            "date": current_time.strftime('%Y-%m-%d'),
            "full_datetime": current_time.isoformat(),
            "timezone_offset": current_time.strftime('%Z%z'),
            "timezone_requested": timezone_str
        })
    except pytz.exceptions.UnknownTimeZoneError:
        return jsonify({"error": f"Unknown timezone: '{timezone_str}'. Please use a valid Olson timezone (e.g., 'America/New_York', 'Europe/London')."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Removed obsolete /api/data endpoint that used DATA_FILE

def summarize_with_gemini(text_to_summarize, original_query):
    if not GEMINI_API_KEY:
        app.logger.error("Gemini API key is not configured. Cannot summarize.")
        return "Summarization service is not configured (missing API key)."

    try:
        # For text summarization, a model like 'gemini-pro' is suitable.
        # Check the Gemini documentation for the latest recommended models for summarization.
        model = genai.GenerativeModel('gemini-pro')

        # Construct a clear prompt for summarization
        prompt = (
            f"Original user query: \"{original_query}\"\n\n"
            f"Please provide a concise summary of the following text, focusing on information relevant to the user's query. "
            f"The text is sourced from web pages found via Google Search based on this query.\n\n"
            f"Text to summarize:\n"
            f"-------------------\n"
            f"{text_to_summarize}\n"
            f"-------------------\n\n"
            f"Concise Summary:"
        )

        # Generate content
        response = model.generate_content(prompt)

        if response.parts:
            # Assuming the response contains the summary in its parts
            summary = "".join(part.text for part in response.parts)
            return summary.strip()
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            # Handle cases where content is blocked
            app.logger.warning(f"Gemini summarization blocked. Reason: {response.prompt_feedback.block_reason}")
            return f"Could not generate summary due to content policy: {response.prompt_feedback.block_reason}."
        else:
            app.logger.warning("Gemini API call succeeded but returned no summary content.")
            return "No summary could be generated from the provided text."

    except Exception as e:
        app.logger.error(f"An error occurred during Gemini summarization: {e}")
        # Check for specific API errors if the library provides them
        # For example, if e has a response attribute with more details
        if hasattr(e, 'response') and e.response:
             app.logger.error(f"Gemini API response error details: {e.response}")
        return f"An error occurred while trying to summarize the content: {str(e)}."

def fetch_content_from_url(url):
    try:
        headers = { # Mimic a browser to avoid simple bot blocks
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10) # 10-second timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4XX or 5XX)

        soup = BeautifulSoup(response.content, 'html.parser')

        # Attempt to extract meaningful text
        # Remove script and style elements
        for script_or_style in soup(["script", "style", "header", "footer", "nav", "aside"]):
            script_or_style.decompose()

        # Get text from common main content tags, then join.
        # This is a simplistic approach and might need refinement for specific sites.
        texts = []
        # Prioritize specific semantic tags if available
        main_content = soup.find('main') or soup.find('article')
        if main_content:
            paragraphs = main_content.find_all('p')
            for p in paragraphs:
                texts.append(p.get_text(separator=' ', strip=True))
        else: # Fallback to finding all paragraphs if no main/article
            paragraphs = soup.find_all('p')
            for i, p in enumerate(paragraphs):
                if i < 20: # Limit paragraphs if no clear main content, to avoid huge irrelevant dumps
                    texts.append(p.get_text(separator=' ', strip=True))

        # If still very little text, try a more generic div search (less reliable)
        if not texts or len(" ".join(texts)) < 200: # Arbitrary threshold for "enough" text
            div_texts = []
            # Look for divs that might contain content, avoiding common non-content classes
            possible_divs = soup.find_all('div', class_=lambda x: x not in ['menu', 'sidebar', 'advertisement', 'footer-links', 'header-nav'])
            for i, div in enumerate(possible_divs):
                if i < 5: # Limit number of divs to process
                     div_text = div.get_text(separator=' ', strip=True)
                     if len(div_text) > 100: # Only consider divs with some substance
                        div_texts.append(div_text)
            if div_texts:
                texts.extend(div_texts)


        full_text = " ".join(texts)

        # Basic cleaning: remove excessive newlines/spaces
        cleaned_text = re.sub(r'\s{2,}', ' ', full_text).strip()

        if not cleaned_text:
            app.logger.info(f"No significant text content found at {url}")
            return None

        # Truncate to a reasonable length for Gemini, e.g., 10k chars (Gemini has token limits)
        # This limit might need to be adjusted based on Gemini's specific model limits
        max_length = 15000
        return cleaned_text[:max_length]

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request error fetching URL {url}: {e}")
        return None
    except Exception as e:
        app.logger.error(f"Error processing content from URL {url}: {e}")
        return None

def perform_google_search(query_string, api_key, cse_id, num_results=3):
    if not api_key:
        app.logger.error("Google API key is not configured.")
        return {"error": "Search functionality is not configured (missing API key)."}
    if not cse_id:
        app.logger.error("Google CSE ID is not configured.")
        return {"error": "Search functionality is not configured (missing CSE ID)."}

    try:
        service = build("customsearch", "v1", developerKey=api_key)
        result = service.cse().list(
            q=query_string,
            cx=cse_id,
            num=num_results
        ).execute()

        search_items = []
        if 'items' in result:
            for item in result['items']:
                search_items.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet")
                })
        return {"items": search_items}
    except HttpError as e:
        app.logger.error(f"An HTTP error occurred during Google Search: {e.resp.status} {e._get_reason()}")
        return {"error": f"Google Search API error: {e._get_reason()}"}
    except Exception as e:
        app.logger.error(f"An unexpected error occurred during Google Search: {e}")
        return {"error": "An unexpected error occurred while searching."}

@app.route('/api/validate_timezone')
def validate_timezone_route():
    tz_param = request.args.get('tz')
    if not tz_param:
        return jsonify({"error": "Missing 'tz' parameter"}), 400
    try:
        pytz.timezone(tz_param)
        return jsonify({"is_valid": True, "timezone": tz_param})
    except pytz.exceptions.UnknownTimeZoneError:
        return jsonify({"is_valid": False, "timezone": tz_param, "error": "Unknown timezone"}), 400
    except Exception as e:
        return jsonify({"is_valid": False, "timezone": tz_param, "error": str(e)}), 500

@app.route('/api/query', methods=['POST'])
def handle_query():
    try:
        query_data = request.get_json()
        if not query_data or 'query' not in query_data:
            return jsonify({"error": "Missing 'query' in request body"}), 400

        user_query = query_data['query']
        app.logger.info(f"Received query: {user_query}") # Good for debugging

        # 1. Call Google Custom Search API
        google_search_result = perform_google_search(user_query, GOOGLE_API_KEY, GOOGLE_CSE_ID, num_results=3)

        if google_search_result.get("error"):
            # If search itself failed, return the error
            return jsonify({"error": f"Search failed: {google_search_result['error']}"}), 500

        search_items = google_search_result.get("items", [])
        if not search_items:
            return jsonify({"results": [{"item": {"summary": "No relevant search results found from Google.", "source": "Google Search"}, "score": 0}], "query_terms": [word for word in user_query.lower().split() if word not in STOP_WORDS], "source_filter": "Google Search + Gemini"}), 200

        # 2. Fetch content from URLs
        fetched_contents = []
        source_urls = [] # Keep track of URLs we successfully fetched from

        for item in search_items: # search_items is from perform_google_search
            url = item.get('link')
            if url:
                app.logger.info(f"Fetching content from URL: {url}")
                text_content = fetch_content_from_url(url)
                if text_content:
                    fetched_contents.append({
                        "url": url,
                        "title": item.get("title", "N/A"),
                        "text": text_content
                    })
                    source_urls.append(url)
                    app.logger.info(f"Successfully fetched and processed content from {url}")
                else:
                    app.logger.warning(f"Could not fetch significant content from {url}")
            if len(fetched_contents) >= 3: # Process max 3 URLs as per user request for search results
                break

        if not fetched_contents: # This check should already be there
            return jsonify({"results": [{"item": {"summary": "Found Google search results, but could not fetch content for summarization.", "source": "Content Fetcher"}, "score": 0}], "query_terms": [word for word in user_query.lower().split() if word not in STOP_WORDS], "source_filter": "Google Search + Gemini"}), 200

        # 3. Summarize with Gemini API
        # Combine text from all fetched sources.
        # Consider adding source URL information or titles if helpful for context,
        # but be mindful of the overall input length to Gemini.
        combined_text_for_gemini = ""
        for i, content_item in enumerate(fetched_contents):
            combined_text_for_gemini += f"Source {i+1} (URL: {content_item['url']}, Title: {content_item['title']}):\n{content_item['text']}\n\n"

        if not combined_text_for_gemini.strip():
             summary = "No text content was successfully fetched from the search results to summarize."
        else:
            app.logger.info(f"Sending combined text (approx {len(combined_text_for_gemini)} chars) to Gemini for summarization.")
            summary = summarize_with_gemini(combined_text_for_gemini.strip(), user_query)

        # Final response structure:
        return jsonify({
            "results": [{"item": {"summary": summary, "source_urls": [fc['url'] for fc in fetched_contents]}, "score": 1}], # source_urls from fetched_contents
            "query_terms": [word for word in user_query.lower().split() if word not in STOP_WORDS], # Keep original query terms
            "source_filter": "Google Search + Gemini"
        })

    except Exception as e:
        app.logger.error(f"Error in /api/query: {e}", exc_info=True)
        #    -     # Handle case where no content could be fetched
        #    -     summary = "Could not fetch content from search results for summarization."
        #    - else:
        #    -     # Combine text or process selectively
        #    -     combined_text_for_gemini = " ".join(ft['text'] for ft in fetched_texts)
        #    -     summary = summarize_with_gemini(combined_text_for_gemini, user_query, GEMINI_API_KEY) # To be implemented

        # Final response structure:
        # return jsonify({
        #     "results": [{"item": {"summary": summary, "source_urls": [ft['url'] for ft in fetched_texts]}, "score": 1}],
        #     "query_terms": [word for word in user_query.lower().split() if word not in STOP_WORDS],
        #     "source_filter": "Google Search + Gemini"
        # })

    except Exception as e:
        app.logger.error(f"Error in /api/query: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred processing your query: " + str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    if request.method == 'POST':
        data = request.get_json()
        if data and 'background_color' in data:
            session['background_color'] = data['background_color']
            return jsonify({"message": "Settings saved successfully.", "background_color": data['background_color']})
        return jsonify({"error": "Invalid data. 'background_color' missing."}), 400

    if request.method == 'GET':
        background_color = session.get('background_color', '#FFFFFF') # Default to white if not set
        return jsonify({"background_color": background_color})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
