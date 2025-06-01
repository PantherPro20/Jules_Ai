# Project Title

This project is designed to [briefly describe the project's purpose].

## Features

* [List key features of the project]

## Technology Stack

* [List technologies used, e.g., Python, Flask, Docker]

## Running the Project

There are two main ways to run this project: using Docker (recommended for ease of use and consistency) or running the components locally.

### Running with Docker (Recommended)

The `Dockerfile` included in the project sets up the environment and runs the web application.

1.  **Build the Docker image:**
    ```bash
    docker build -t scraper-ai-app .
    ```

2.  **Run the Docker container:**
    To run the container and have the web application accessible on `http://localhost:5000`:
    ```bash
    docker run -p 5000:5000 scraper-ai-app
    ```

3.  **Running with Persistent Data (Important for Scrapers):**
    The scrapers generate data that the web application uses. To ensure this data persists and can be updated:
    *   Create a directory on your host machine to store the data, for example:
        ```bash
        mkdir my_persistent_data
        ```
    *   **Run the scraper first (on your host machine)** to populate this directory. Ensure the `scraper/main_scraper.py` is configured to output `scraped_data.json` into this `my_persistent_data` directory (or copy it there after running).
        ```bash
        python scraper/main_scraper.py
        # (Then ensure my_persistent_data/scraped_data.json exists)
        ```
    *   Run the Docker container with a volume mount:
        ```bash
        docker run -p 5000:5000 -v "$(pwd)/my_persistent_data:/app/data" scraper-ai-app
        ```
        *(Replace `$(pwd)/my_persistent_data` with the absolute path to your data directory if needed).*

    The web application will be available at `http://localhost:5000`.

### Running Locally (Without Docker)

1.  **Prerequisites:**
    *   Python 3.7+
    *   pip (Python package installer)

2.  **Set up a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Install the required Python packages from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The `webapp` also has its own `requirements.txt` (`webapp/requirements.txt`). For simplicity, the main `requirements.txt` should ideally cover all dependencies. If running components separately, ensure dependencies for each part are installed.*

4.  **Run the Scrapers:**
    To collect data for the application, run the main scraper script:
    ```bash
    python scraper/main_scraper.py
    ```
    This will create/update the `data/scraped_data.json` file.

5.  **Run the Web Application:**
    Once the data is scraped, you can run the Flask web application:
    ```bash
    python webapp/app.py
    ```
    The application will typically be available at `http://localhost:5000`.
