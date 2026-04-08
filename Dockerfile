FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server source code
COPY server/ .

# HF Spaces uses port 7860
EXPOSE 7860

# Health check — ensures /health returns 200
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')"

# Start the FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
