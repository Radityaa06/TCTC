FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app

ENV PYTHONPATH=/app/server

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code including pre-compiled static frontend bundle
COPY . .

# Install xvfb if it's not present (just to be safe)
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

EXPOSE 8000

CMD ["xvfb-run", "-a", "--server-args=-screen 0 1920x1080x24", "python3", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
