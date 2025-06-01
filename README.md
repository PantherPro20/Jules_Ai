# AI Query Engine with Google Search & Gemini

## Overview

This project is a web application that takes a user's query, performs a Google search to find relevant web pages, fetches content from the top search results, and then uses the Gemini API to generate a concise summary of the combined information. This provides users with quick, AI-powered answers based on real-time web data.

## Features

*   **Real-time Information Lookup:** Utilizes Google Custom Search API to find up-to-date information.
*   **Content Fetching:** Retrieves textual content from the top search result URLs.
*   **AI-Powered Summarization:** Leverages the Gemini API to provide concise summaries of the fetched content, tailored to the user's query.
*   **Web Interface:** Simple Flask-based web UI for submitting queries and viewing results.
*   **Customizable Appearance:** Users can change the background color of the web interface.

## Technology Stack

*   **Backend:** Python, Flask
*   **APIs:**
    *   Google Custom Search JSON API (via `google-api-python-client`)
    *   Google Gemini API (via `google-generativeai`)
*   **Web Content Fetching:** `requests`, `BeautifulSoup4`
*   **Deployment:** Docker (optional)
*   **Timezone Handling:** `pytz`

## Setup and Configuration

### API Keys

To use this application, you will need API keys for the following Google services:

1.  **Google Cloud API Key (for Custom Search JSON API):**
    *   Obtain this from the [Google Cloud Console](https://console.cloud.google.com/). You'll need to enable the "Custom Search API".
2.  **Google AI Studio API Key (for Gemini API):**
    *   Obtain this from [Google AI Studio (formerly MakerSuite)](https://aistudio.google.com/).
3.  **Google Custom Search Engine ID (CSE ID):**
    *   Create a Custom Search Engine at [Google's Programmable Search Engine control panel](https://programmablesearchengine.google.com/).
    *   Configure it to search the entire web or specific sites you are interested in.
    *   The CSE ID can be found in the "Basic Information" section of your search engine's setup. A default CSE ID (`63bdfe80d8bfe4a62`) is provided in the application code as a fallback if the environment variable is not set, but it's highly recommended to use your own.

### Environment Variables

You **must** set the following environment variables before running the application:

*   `GOOGLE_API_KEY`: Your Google Cloud API key.
*   `GEMINI_API_KEY`: Your Google AI Studio (Gemini) API key.
*   `GOOGLE_CSE_ID`: Your Custom Search Engine ID. (While there's a default, setting this is preferred).

### Using a `.env` File for API Keys (Local Development)

For local development, you can use a `.env` file to manage your API keys conveniently. The application will automatically load variables defined in this file thanks to the `python-dotenv` library.

1.  **Create a file named `.env`** in the root directory of the project (the same directory as `requirements.txt` and `webapp/`).

2.  **Add your API keys** to the `.env` file in the following format:
    ```env
    GOOGLE_API_KEY='YourActualGoogleApiKey'
    GEMINI_API_KEY='YourActualGeminiApiKey'
    GOOGLE_CSE_ID='YourActualGoogleCseId'
    ```
    Replace the placeholder values with your actual keys and ID. Do not use quotes around the values in the `.env` file unless they are part of the key itself (which is rare). For example:
    ```env
    GOOGLE_API_KEY=YourActualGoogleApiKeyWithoutQuotes
    GEMINI_API_KEY=YourActualGeminiApiKeyWithoutQuotes
    GOOGLE_CSE_ID=YourActualGoogleCseIdWithoutQuotes
    ```

3.  **Security Note:** The `.env` file is included in `.gitignore` (as of a previous setup step), so it will not (and should not) be committed to your Git repository. This keeps your secrets safe.

When you run `python webapp/app.py` locally, these variables will be loaded into the environment and used by the application. For Docker deployments, you should still pass environment variables using the `-e` flag as described in the "Running with Docker" section, as the `.env` file is not copied into the Docker image for security and best practices.

## Running Locally

1.  **Prerequisites:**
    *   Python 3.7+
    *   `pip` (Python package installer)

2.  **Set up a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Environment Variables:**
    *   **Linux/macOS:**
        ```bash
        export GOOGLE_API_KEY='YOUR_GOOGLE_API_KEY'
        export GEMINI_API_KEY='YOUR_GEMINI_API_KEY'
        export GOOGLE_CSE_ID='YOUR_CSE_ID' # e.g., 63bdfe80d8bfe4a62
        ```
    *   **Windows (PowerShell):**
        ```powershell
        $env:GOOGLE_API_KEY='YOUR_GOOGLE_API_KEY'
        $env:GEMINI_API_KEY='YOUR_GEMINI_API_KEY'
        $env:GOOGLE_CSE_ID='YOUR_CSE_ID' # e.g., 63bdfe80d8bfe4a62
        ```
    *Replace placeholders with your actual keys and ID.*

5.  **Run the Application:**
    ```bash
    python webapp/app.py
    ```
    The application will typically be available at `http://localhost:5000`.

## Running with Docker

1.  **Build the Docker Image:**
    ```bash
    docker build -t ai-query-app .
    ```

2.  **Run the Docker Container:**
    You must pass your API keys and CSE ID as environment variables to the container.
    ```bash
    docker run -p 5000:5000 \
      -e GOOGLE_API_KEY='YOUR_GOOGLE_API_KEY' \
      -e GEMINI_API_KEY='YOUR_GEMINI_API_KEY' \
      -e GOOGLE_CSE_ID='YOUR_CSE_ID' \
      ai-query-app
    ```
    *Replace `YOUR_GOOGLE_API_KEY`, `YOUR_GEMINI_API_KEY`, and `YOUR_CSE_ID` with your actual credentials.*

## Usage

1.  Open your web browser and navigate to `http://localhost:5000`.
2.  Enter your query into the input field and press "Send" or hit Enter.
3.  The application will display a summary based on Google Search results and Gemini AI.
4.  You can change the timezone and background color using the settings icon in the header.
