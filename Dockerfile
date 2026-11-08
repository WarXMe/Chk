FROM python:3.11-slim

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# /data is the Render persistent disk mount point
RUN mkdir -p /data

ENV DB_PATH=/data/xboxchkr.db
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "main.py"]
