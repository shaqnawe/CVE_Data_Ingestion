FROM python:3.11-slim

WORKDIR /app/backend

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/app/backend/entrypoint.sh"]