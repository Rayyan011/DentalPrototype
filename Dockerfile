# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Explicitly set the Python path (critical!)
ENV PYTHONPATH=/app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the project files into the container
COPY . /app/

# Make manage.py executable
RUN chmod +x manage.py

# Run database migrations

# Collect static files
RUN python manage.py collectstatic --noinput

# Create a directory for static files to be served
RUN mkdir -p /app/staticfiles

# Health check
HEALTHCHECK CMD python -c "import django; django.setup(); from django.db import connections; connections['default'].ensure_connection();"

# Set the entrypoint to run the server using Gunicorn
CMD ["gunicorn", "dentaclinic.wsgi:application", "--bind", "0.0.0.0:8000"]
