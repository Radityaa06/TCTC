FROM python:3.10-slim

WORKDIR /app
ENV PYTHONPATH=/app/server

# Install core python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ONLY Chromium and its system dependencies (including xvfb) to save massive amounts of time and space
RUN playwright install chromium --with-deps

# Copy source code
COPY . .

EXPOSE 8000

CMD ["xvfb-run", "-a", "--server-args=-screen 0 1920x1080x24", "python3", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
