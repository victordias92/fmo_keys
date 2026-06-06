FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgtk-3-0 \
    libgstreamer1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# index.html em assets/ sobrescreve a UI do Flet e deixa a pagina em branco
RUN rm -f assets/index.html assets/service-worker.js

ENV FLET_FORCE_WEB_SERVER=true

CMD ["python", "main.py"]
