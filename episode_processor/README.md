# Podcast Transkriptions-Tool

Dieses Projekt ist ein Python-Skript, das Podcast-Episoden von einem RSS-Feed herunterlädt und mit einem Whisper-Modell transkribiert.

## Voraussetzungen

- Docker
- NVIDIA Container Toolkit (falls GPU-Unterstützung benötigt wird)

## Einrichtung


### 1. Docker-Image erstellen

Wenn nötig erstelle das Docker-Image mit dem folgenden Befehl:

```bash
docker build -t transcribe-app .
```

### 2. Verzeichnisse erstellen

Erstelle die Verzeichnisse `downloads` und `text` auf deinem Host-System, um die heruntergeladenen und transkribierten Dateien zu speichern:

```bash
mkdir -p downloads text
```

## Verwendung

### Docker-Container ausführen

Führe den Docker-Container mit den folgenden Befehlen aus. Dies mountet die Verzeichnisse `downloads` und `text` in den Container, sodass die Dateien auf dem Host-System verfügbar sind:

```bash
docker run -it --rm --gpus all \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/text:/app/text \
  transcribe-app
```

### Beschreibung der Skriptfunktionen

- **get_episode_links()**: Ruft die Links zu den Podcast-Episoden aus dem RSS-Feed ab.
- **load_episodes_df()**: Lädt die bereits heruntergeladenen Episoden aus einer CSV-Datei.
- **add_new_episodes()**: Fügt neue Episoden zur CSV-Datei hinzu.
- **download_episode()**: Lädt eine Podcast-Episode von einer gegebenen URL herunter.
- **delete_download_folder()**: Löscht den Download-Ordner und dessen Inhalte.
- **process_episode()**: Verarbeitet eine Episode mit dem Whisper-Modell und speichert die Transkription in einer Textdatei.
- **prepare_whisper_model()**: Bereitet das Whisper-Modell für die Spracherkennung vor.

## Konfiguration

- **RSS_FEED_URL**: Die URL des RSS-Feeds, von dem die Episoden heruntergeladen werden.
- **MODEL_ID**: Das Whisper-Modell, das für die Transkription verwendet wird.

## Hinweise

- Stelle sicher, dass du die NVIDIA Container Toolkit installiert hast, wenn du GPU-Unterstützung benötigst.
- Die heruntergeladenen und transkribierten Dateien werden in den Verzeichnissen `downloads` und `text` gespeichert und sind auf dem Host-System verfügbar.


### Modellauswahl

Im ursprünglichen Skript wurde das Modell "primeline/whisper-large-v3-turbo-german" verwendet. Bei der Transkription der ersten Audiodatei auf einer RTX 3090 Ti mit einer batch_size von 8 dauerte der Vorgang etwa 4 Minuten. Dabei verbrauchte die Grafikkarte laut nvidia-smi etwa 350 Watt.

Durch den Wechsel zu dem Modell "primeline/whisper-tiny-german-1224" und einer batch_size von 32 konnte die Bearbeitungszeit auf etwa 2 Minuten und 40 Sekunden reduziert werden. Gleichzeitig sank der Energieverbrauch auf etwa 230 Watt. Obwohl die Ergebnisse des neuen Modells nicht explizit überprüft wurde, sind die schnellere Bearbeitungszeit und der geringere Energieverbrauch für mich ausreichende Gründe, dieses Modell zu verwenden.