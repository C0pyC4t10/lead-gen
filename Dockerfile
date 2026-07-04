FROM python:3.11-slim

WORKDIR /app

RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m playwright install chromium --with-deps

COPY . .

EXPOSE 8800

CMD ["sh", "-c", "\
  mkdir -p /app/data/collected_leads /app/data/qualified_leads /app/data/avatars && \
  rm -rf /app/collected_leads /app/qualified_leads /app/avatars && \
  ln -sf /app/data/collected_leads /app/collected_leads && \
  ln -sf /app/data/qualified_leads /app/qualified_leads && \
  ln -sf /app/data/avatars /app/avatars && \
  touch /app/data/auth.db && \
  ln -sf /app/data/auth.db /app/auth.db && \
  python server.py"]
