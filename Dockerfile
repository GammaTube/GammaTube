# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables
# Setting PYTHONUNBUFFERED to 1 ensures that Python outputs everything to the console without buffering
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
# Use --no-cache-dir to prevent caching and keep the image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port that the Flask app runs on
EXPOSE 5000

# Define the command to run the application
# This will allow Flask to run in development mode with reloading
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
