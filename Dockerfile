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
# docker build -t scraper-ai-app .
#
# To run the container (basic):
# docker run -p 5000:5000 scraper-ai-app
#
# To run with persistent data (recommended):
# 1. Create a 'data' directory on your host: mkdir my_persistent_data
# 2. Run the main_scraper.py to populate it: python scraper/main_scraper.py (ensure its output is in my_persistent_data)
#    (Or copy your existing data/scraped_data.json into my_persistent_data/scraped_data.json)
# 3. Run container with volume mount:
#    docker run -p 5000:5000 -v "$(pwd)/my_persistent_data:/app/data" scraper-ai-app
#    (Replace $(pwd)/my_persistent_data with the absolute path to your data directory if needed)
#
# The web application will be available at http://localhost:5000
#
# Note: The main_scraper.py is intended to be run on the host to update the
# data in the mounted volume, or to update data/scraped_data.json before rebuilding the image.
# Running scrapers inside the container would require them to also write to this /app/data volume.
