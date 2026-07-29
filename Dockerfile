FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
ENV PYTHONPATH=/app/server

# Install Python, pip, and xvfb
RUN apt-get update && apt-get install -y python3 python3-pip xvfb curl && rm -rf /var/lib/apt/lists/*

# Install core python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install ONLY Chromium and its system dependencies
RUN playwright install chromium --with-deps

# Copy source code
COPY . .

EXPOSE 8000

CMD ["xvfb-run", "-a", "--server-args=-screen 0 1920x1080x24", "python3", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
