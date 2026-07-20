FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code, models, static dashboard, and scripts
COPY src/ ./src/
COPY data/ ./data/
COPY static/ ./static/
COPY scripts/ ./scripts/

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV KLOUDTECH_BASE_URL="https://api.kloudtechsea.com/api/v1"

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
