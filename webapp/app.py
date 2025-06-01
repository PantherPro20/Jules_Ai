from flask import Flask, jsonify, render_template, request, session
import json
import os
import datetime
import pytz # For timezone handling
import re # For simple tokenization and keyword extraction

app = Flask(__name__)
app.secret_key = os.urandom(24) # Or a fixed secret string for development

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "../data/scraped_data.json")

# Basic list of English stop words
STOP_WORDS = set([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
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

@app.route('/api/data')
def get_data():
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify({"error": "Data file not found. Please run the scrapers first."}), 404

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
        return jsonify(scraped_data)
    except Exception as e:
        return jsonify({"error": "Could not read or parse data file: " + str(e)}), 500

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

        raw_query = query_data['query'].lower()

        # Simple tokenization (split by space and remove punctuation)
        words = re.findall(r'\b\w+\b', raw_query)

        # Filter out stop words
        keywords = [word for word in words if word not in STOP_WORDS]

        # Identify source filter
        target_source = None
        temp_keywords = []
        for keyword in keywords:
            if keyword in KNOWN_SOURCES:
                target_source = KNOWN_SOURCES[keyword]
            # Check if it's part of a multi-word source like "bbc news"
            elif any(f"{keyword} {next_word}" in KNOWN_SOURCES for next_word in keywords[keywords.index(keyword)+1:] if keywords.index(keyword)+1 < len(keywords)):
                # This is a simplification; proper entity recognition is complex.
                # Example: "bbc news" -> target_source = "BBC News"
                # For now, simple keywords matching KNOWN_SOURCES keys is primary.
                pass # Already handled if keyword is a key in KNOWN_SOURCES
            else:
                temp_keywords.append(keyword)
        keywords = temp_keywords

        if not keywords and not target_source: # If only stop words or no actual query terms
             return jsonify({"results": [], "message": "Please provide more specific keywords."})


        # Load data
        if not os.path.exists(DATA_FILE):
            return jsonify({"error": "Data file not found."}), 500
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            all_items = json.load(f)

        results = []
        for item in all_items:
            # Source filtering
            if target_source and item.get('source') != target_source:
                continue

            match_score = 0
            text_to_search = (item.get('title', '') + ' ' + item.get('summary', '')).lower()

            if not keywords: # If only a source filter was provided
                if target_source and item.get('source') == target_source:
                    match_score = 1 # Give a basic score to include it
            else:
                for kw in keywords:
                    if kw in text_to_search:
                        match_score += text_to_search.count(kw) # Simple count based score

            if match_score > 0:
                results.append({"item": item, "score": match_score})

        # Sort results by score, descending
        results.sort(key=lambda x: x['score'], reverse=True)

        # Limit results (e.g., top 10)
        results = results[:10]

        return jsonify({"results": results, "query_terms": keywords, "source_filter": target_source})

    except Exception as e:
        app.logger.error(f"Error in /api/query: {e}", exc_info=True) # Log the full error
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
