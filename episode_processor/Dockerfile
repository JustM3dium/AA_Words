# Verwende ein offizielles Python-Image als Basis
FROM python:3.12-slim

# Installiere ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die Anforderungen und installiere sie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest des Anwendungsverzeichnisses in den Container
COPY . .

# Stelle sicher, dass die Download- und Textordner vorhanden sind
RUN mkdir -p downloads text

# Der Befehl, der ausgeführt wird, wenn der Container startet
CMD ["python", "aa_to_text.py"]
