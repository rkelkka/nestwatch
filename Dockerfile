# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install OpenGL and GLib libraries (including libgthread-2.0)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for the Flask API
EXPOSE 5000

# Run the Flask API when the container starts
CMD ["python", "src/nestwatch.py"]

