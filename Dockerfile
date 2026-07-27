FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend package manifests and install all dependencies
COPY frontend/package*.json frontend/
RUN cd frontend && npm install --include=dev

# Copy source code and build production static bundle
COPY . .
RUN cd frontend && npm run build

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
