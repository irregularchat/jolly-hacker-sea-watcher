FROM python:3.11-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ARG TEMPORAL_API_KEY
ENV TEMPORAL_API_KEY=${TEMPORAL_API_KEY}
ENV PYTHONUNBUFFERED=1

# Run the worker
CMD ["python", "worker.py"] 