# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY app/requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY app /app

# Expose port 8000 for Flask
EXPOSE 8000

# Command to run the Flask app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
