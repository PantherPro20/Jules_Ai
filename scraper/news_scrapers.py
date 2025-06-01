import requests
from bs4 import BeautifulSoup
import json
import os
import datetime

# Ensure data directory exists (relative to the script's location in scraper/ )
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
                return []
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def scrape_bbc_news(max_articles=5):
    print("Scraping BBC News...")
    bbc_url = "https://www.bbc.com/news"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    new_entries = []
    try:
        response = requests.get(bbc_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # BBC structure can change. This is an example selector.
        # Looking for promo-headlines, common on BBC.
        # We need to find elements that likely contain a headline and a link.
        # This selector might need adjustment: 'div.gs-c-promo-body h3.gs-c-promo-heading__title'
        # Let's try a broader approach first for links, then get titles.

        articles_found_count = 0
        # Common pattern: articles are often within <a> tags that have an href.
        # And the headline text is often within that <a> tag or a child element like <h3> or <p>

        # Attempt 1: Find <a> tags with hrefs under common content containers
        # Note: Selectors are highly dependent on current site structure.
        # This is a common pattern for news sites: list of links with headlines.
        # For BBC, links are often within 'gs-c-promo' containers.
        # Headlines are often in <h3> with class 'gs-c-promo-heading__title'
        # Links are the parent <a> tag of these <h3>s.

        promo_links = soup.select('a.gs-c-promo-heading[href]') # Selects <a> tags with class and href

        if not promo_links: # Fallback if specific selector fails
             promo_links = soup.select('div[class*="promo"] a[href]') # More generic

        for link_tag in promo_links:
            if articles_found_count >= max_articles:
                break

            href = link_tag.get('href')
            title_tag = link_tag.find(['h3', 'p', 'span'], class_=lambda x: x and 'title' in x.lower()) # Look for title-like classes
            if not title_tag:
                 title_tag = link_tag.find(['h3','p']) # More generic title find

            title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(strip=True)


            if href and title:
                if not href.startswith('http'):
                    href = "https://www.bbc.com" + href

                # Simple summary - often the first <p> after the heading or within the promo body
                summary_tag = None
                parent_promo = link_tag.find_parent(lambda tag: 'promo' in ' '.join(tag.get('class', [])))
                if parent_promo:
                    summary_tag = parent_promo.find('p', class_=lambda x: x and ('summary' in x.lower() or 'strapline' in x.lower()))
                    if not summary_tag: # More generic <p>
                        summary_tag = parent_promo.find('p')

                summary = summary_tag.get_text(strip=True) if summary_tag else "Summary not readily available."


                entry = {
                    "title": title,
                    "summary": summary,
                    "url": href,
                    "source": "BBC News",
                    "scraped_at": datetime.datetime.utcnow().isoformat() + "Z"
                }
                new_entries.append(entry)
                articles_found_count += 1

        print(f"Found {len(new_entries)} articles from BBC News.")

    except requests.exceptions.RequestException as e:
        print(f"Error scraping BBC News: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with BBC News: {e}")
    return new_entries

def scrape_cnn_news(max_articles=5):
    print("Scraping CNN News...")
    cnn_url = "https://www.cnn.com" # Focus on top news or a specific section if too broad
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    new_entries = []
    try:
        response = requests.get(cnn_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        articles_found_count = 0
        # CNN structure: articles often in <article> tags or divs with 'card', 'container', 'headline'
        # Links are within these, often with a specific data-linktype="article"
        # Or look for <a> tags with 'href' that seem to point to articles.
        # Example: soup.select('a[data-linktype="article"]')
        # More general: find links with headlines. Headlines often in <span> or <h2>, <h3>

        # This selector aims for common article links. Might need tuning.
        # It looks for links whose text is wrapped in a span, common for CNN headlines.
        article_links = soup.select('a[href^="/"][data-linktype="article"]') # Links starting with / and specific data-linktype
        if not article_links:
            # Fallback: Find elements with 'headline' in class and get their parent link
            headline_elements = soup.select('[class*="headline"] span')
            temp_links = set()
            for hl_el in headline_elements:
                parent_a = hl_el.find_parent('a', href=True)
                if parent_a and parent_a['href'].startswith('/'):
                     temp_links.add(parent_a)
            article_links = list(temp_links)


        for link_tag in article_links:
            if articles_found_count >= max_articles:
                break

            href = link_tag.get('href')
            # Headline text is often directly in a child span or the link itself
            title_element = link_tag.find('span', {'data-editable': 'headline'}) or link_tag.find_all(string=True, recursive=False)
            title = ""
            if isinstance(title_element, list): # from find_all
                title = ' '.join(t.strip() for t in title_element if t.strip()).strip()
            elif title_element: # from find
                title = title_element.get_text(strip=True)

            if not title: # if still no title, try the link's own text
                title = link_tag.get_text(strip=True)

            if href and title:
                if not href.startswith('http'):
                    href = "https://www.cnn.com" + href

                # CNN summaries are harder from main page, often need to visit article.
                # For now, placeholder.
                summary = "Summary not readily available from headlines page."

                entry = {
                    "title": title,
                    "summary": summary,
                    "url": href,
                    "source": "CNN News",
                    "scraped_at": datetime.datetime.utcnow().isoformat() + "Z"
                }
                new_entries.append(entry)
                articles_found_count += 1

        print(f"Found {len(new_entries)} articles from CNN News.")

    except requests.exceptions.RequestException as e:
        print(f"Error scraping CNN News: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with CNN News: {e}")
    return new_entries


if __name__ == "__main__":
    all_data = load_existing_data()
    existing_urls = {item['url'] for item in all_data if 'url' in item}

    new_bbc_articles = scrape_bbc_news(max_articles=5)
    new_cnn_articles = scrape_cnn_news(max_articles=5)

    added_count = 0
    for article_list in [new_bbc_articles, new_cnn_articles]:
        for article in article_list:
            if article['url'] not in existing_urls:
                all_data.append(article)
                existing_urls.add(article['url'])
                added_count += 1
            else:
                print(f"Skipping already scraped article: {article['title'][:30]}... ({article['source']})")

    save_data(all_data)
    if added_count > 0:
        print(f"Successfully scraped and added {added_count} new articles from BBC/CNN.")
    else:
        print("No new articles were added from BBC/CNN (or they were already scraped).")
    print(f"Data saved to {os.path.abspath(DATA_FILE)}")

    # Optionally print some of the newly added data structure
    # for item in all_data[-added_count:]:
    #    print(f"- {item['source']}: {item['title']}")
