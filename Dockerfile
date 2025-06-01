# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by some Python packages (if any)
# For example, for 'lxml' or other packages with C extensions:
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libxml2-dev libxslt1-dev && rm -rf /var/lib/apt/lists/*
# For this project, current dependencies (Flask, requests, bs4, wikipedia, pytz) usually don't need extra system libs.

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
# This includes 'webapp', 'scraper', and 'data' directories.
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable for Flask
ENV FLASK_APP=webapp/app.py
ENV FLASK_RUN_HOST=0.0.0.0
# ENV FLASK_ENV=production # Uncomment for production, but debug=True is in app.py for now

# Run app.py when the container launches
# The CMD should be structured as a JSON array for exec form
CMD ["flask", "run"]

# Instructions for user:
# --------------------
# To build the image:
# docker build -t ai-query-app . # Changed name slightly for new functionality
#
# To run the container:
# You MUST provide your API keys as environment variables.
# Replace 'YOUR_GOOGLE_API_KEY', 'YOUR_GEMINI_API_KEY', and 'YOUR_GOOGLE_CSE_ID'
# with your actual keys and CSE ID.
#
# docker run -p 5000:5000 \
#   -e GOOGLE_API_KEY='YOUR_GOOGLE_API_KEY' \
#   -e GEMINI_API_KEY='YOUR_GEMINI_API_KEY' \
#   -e GOOGLE_CSE_ID='63bdfe80d8bfe4a62' \ # Or your specific CSE ID if different
#   ai-query-app
#
# The web application will be available at http://localhost:5000
#
# The application requires these API keys to contact Google Search and Gemini services.
# The GOOGLE_CSE_ID is pre-filled with the one provided during development (63bdfe80d8bfe4a62),
# but can also be overridden via the -e flag if needed.
