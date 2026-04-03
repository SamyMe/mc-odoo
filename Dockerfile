FROM python:3.12-slim

WORKDIR /app

# Ensure CA certificates are available for outbound SSL
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# Install uv for fast package installs
RUN pip install --no-cache-dir uv

# Install Python dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application files
COPY proxy.py .
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
