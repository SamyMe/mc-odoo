FROM python:3.12-slim

WORKDIR /app

# Install uv for fast package installs
RUN pip install --no-cache-dir uv

# Install Python dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application files
COPY proxy.py .
COPY start.sh .
RUN chmod +x start.sh

# Railway injects $PORT at runtime — do not hardcode it
CMD ["./start.sh"]
