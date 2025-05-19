# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory inside the container
WORKDIR /app

# Install system dependencies
# libpq-dev and gcc are often needed for psycopg2 (PostgreSQL adapter) if it compiles from source
RUN apt-get update && apt-get install -y libpq-dev gcc build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app/

# Expose the port Gunicorn will run on (internal to Docker network)
EXPOSE 8000

# The CMD will be specified in docker-compose.yml to run Gunicorn
# Example: CMD ["gunicorn", "--bind", "0.0.0.0:8000", "dentaclinic.wsgi:application"]
