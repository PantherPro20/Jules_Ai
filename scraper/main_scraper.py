import subprocess
import sys
import os

# Ensure the script can find sibling modules (wikipedia_scraper, news_scrapers)
# This assumes main_scraper.py is in the 'scraper' directory.
# And that it's run from the project root, or paths are adjusted.

# If running from project root: python scraper/main_scraper.py
# Then imports in child scripts like `from .wikipedia_scraper import scrape_wikipedia` would fail
# if they are not structured as a package.
# For simplicity, let's call them as separate processes, which is more robust for standalone scripts.

def run_scraper(script_name):
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    print(f"Running {script_name}...")
    try:
        # Ensure python3 is used. sys.executable is the current python interpreter.
        process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            print(f"{script_name} completed successfully.")
            if stdout:
                print(f"Output from {script_name}:\n{stdout.decode()}")
        else:
            print(f"Error running {script_name}. Return code: {process.returncode}")
            if stdout:
                print(f"Output (stdout) from {script_name}:\n{stdout.decode()}")
            if stderr:
                print(f"Error output (stderr) from {script_name}:\n{stderr.decode()}")
    except FileNotFoundError:
        print(f"Error: Scraper script {script_path} not found.")
    except Exception as e:
        print(f"An unexpected error occurred while trying to run {script_name}: {e}")

if __name__ == "__main__":
    print("Starting all scrapers...")

    # It's important that the individual scraper scripts handle their own dependencies
    # (like installing 'wikipedia' if not present) or that dependencies are pre-installed.
    # The wikipedia_scraper.py already has a pip install check.
    # The news_scrapers.py relies on requests/bs4 being present.

    run_scraper("wikipedia_scraper.py")
    run_scraper("news_scrapers.py")

    print("All scrapers finished.")
    # The data is saved by individual scrapers into data/scraped_data.json
    data_file_path = os.path.join(os.path.dirname(__file__), "../data/scraped_data.json")
    print(f"Consolidated data should be available in {os.path.abspath(data_file_path)}")
