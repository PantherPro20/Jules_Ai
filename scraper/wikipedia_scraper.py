import wikipedia
import json
import os
import datetime

# Ensure data directory exists
DATA_DIR = "data" # Changed path to be relative to the execution directory /app
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DATA_FILE = os.path.join(DATA_DIR, "scraped_data.json")

def load_existing_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] # Return empty list if file is empty or corrupted
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def scrape_wikipedia(topics, num_sentences=3):
    print(f"Starting Wikipedia scraping for topics: {topics}...")
    all_data = load_existing_data()
    existing_urls = {item['url'] for item in all_data if 'url' in item}
    new_entries_count = 0

    for topic in topics:
        print(f"Searching Wikipedia for: {topic}")
        try:
            # Search for pages related to the topic
            search_results = wikipedia.search(topic, results=5) # Get a few search results
            if not search_results:
                print(f"No Wikipedia pages found for '{topic}'.")
                continue

            for page_title in search_results:
                try:
                    page = wikipedia.page(page_title, auto_suggest=False) # auto_suggest=False to avoid issues with similar titles
                    if page.url in existing_urls:
                        print(f"Skipping already scraped page: {page.title} ({page.url})")
                        continue

                    print(f"Scraping: {page.title} ({page.url})")
                    summary = wikipedia.summary(page_title, sentences=num_sentences, auto_suggest=False)

                    entry = {
                        "title": page.title,
                        "summary": summary,
                        "url": page.url,
                        "source": "Wikipedia",
                        "scraped_at": datetime.datetime.utcnow().isoformat() + "Z"
                    }
                    all_data.append(entry)
                    existing_urls.add(page.url)
                    new_entries_count += 1
                except wikipedia.exceptions.PageError:
                    print(f"Wikipedia page '{page_title}' not found or is ambiguous. Skipping.")
                except wikipedia.exceptions.DisambiguationError as e:
                    print(f"Disambiguation page found for '{page_title}'. Options: {e.options[:3]}... Skipping for now.")
                except Exception as e:
                    print(f"An error occurred while scraping '{page_title}': {e}")
        except Exception as e:
            print(f"An error occurred while searching for topic '{topic}': {e}")

    save_data(all_data)
    if new_entries_count > 0:
        print(f"Successfully scraped and added {new_entries_count} new entries from Wikipedia.")
    else:
        print("No new entries were added from Wikipedia.")

if __name__ == "__main__":
    # Example usage:
    # Check if python3-wikipedia is installed, if not, install it
    try:
        __import__('wikipedia')
    except ImportError:
        print("wikipedia library not found. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "python3-wikipedia"])
        print("wikipedia library installed successfully.")
        # It's generally better to install via requirements.txt, but for a standalone script test:
        # You might need to re-run the script after installation if pip is in a different scope.
        __import__('wikipedia') # try importing again

    topics_to_scrape = ["Artificial Intelligence", "Python (programming language)", "Web scraping"]
    scrape_wikipedia(topics_to_scrape)
    print(f"Data saved to {os.path.abspath(DATA_FILE)}")

    # Test loading and printing some data
    # data = load_existing_data()
    # for item in data[:2]:
    #    print(item['title'])
