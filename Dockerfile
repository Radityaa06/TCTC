FROM python:3.11-slim

# Install Node.js, xvfb, & system dependencies for Playwright
RUN apt-get update && apt-get install -y curl gnupg xvfb && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs gcc g++ make && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python packages + playwright browser dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps

# Copy frontend and build
COPY frontend/package.json frontend/
RUN cd frontend && npm install

COPY . .

RUN cd frontend && npm run build

EXPOSE 8000

CMD ["xvfb-run", "-a", "python3", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
