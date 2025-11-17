# Use an official Python 3.10 slim-version image as the base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Set an environment variable for the port
ENV PORT 8080

# Copy your requirements.txt file into the container
COPY requirements.txt .

# --- NEW STEP ---
# Install the small, CPU-only version of PyTorch *before*
# your requirements. This stops sentence-transformers
# from downloading the huge GPU version.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Now install the rest of your libraries
RUN pip install --no-cache-dir -r requirements.txt

# --- TYPO FIX ---
# Copy the rest of your project's files (app.py, models, etc.)
# Make sure this has ONE dot, not two.
COPY . .

# Tell Google Cloud how to start your app
CMD gunicorn --bind 0.0.0.0:$PORT app:app