import logging
import os
import re
import time
import pandas as pd
import requests
import torch
from bs4 import BeautifulSoup
from tqdm import tqdm
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
RSS_FEED_URL = "https://alman-arabica.podcaster.de/alman-arabica.rss"
EPISODES_CSV = "episodes.csv"
DOWNLOAD_FOLDER = "downloads"
TEXT_FOLDER = "text"
MODEL_ID = "primeline/whisper-tiny-german-1224"


def get_episode_links():
    """Fetches episode links from the Alman Arabica RSS feed."""
    try:
        response = requests.get(RSS_FEED_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        episodes = []
        for item in items:
            title = item.find("title").text.strip()
            enclosure = item.find("enclosure")
            media_url = enclosure["url"] if enclosure else None
            match = re.search(r"#(\d+)", title)
            episode_number = int(match.group(1)) if match else None

            if episode_number and media_url:
                episodes.append({
                    "number": episode_number,
                    "title": title,
                    "link": media_url,
                    "state": ""
                })

        return pd.DataFrame(episodes).sort_values(by="number").reset_index(drop=True)
    except Exception as e:
        logger.error(f"Error fetching episode links: {e}")
        return pd.DataFrame()


def load_episodes_df(file_path=EPISODES_CSV):
    """Loads the episodes DataFrame from a CSV file."""
    if not os.path.exists(file_path):
        logger.warning(f"File {file_path} does not exist. Creating an empty file.")
        with open(file_path, 'w') as file:
            file.write("")
        return pd.DataFrame(columns=['number', 'title', 'link', 'state'])

    try:
        df_episodes = pd.read_csv(file_path)
        if df_episodes.empty:
            logger.warning("The loaded DataFrame is empty.")
        return df_episodes
    except Exception as e:
        logger.error(f"Error loading episodes: {e}")
        return pd.DataFrame(columns=['number', 'title', 'link', 'state'])

def add_new_episodes(df_episodes):
    """Adds new episodes to the DataFrame and saves it to a CSV file."""
    df_link = get_episode_links()
    if df_episodes.empty:
        df_episodes = pd.DataFrame(columns=['number', 'title', 'link', 'state'])

    new_episodes = df_link[~df_link['number'].isin(df_episodes['number'])]
    if not new_episodes.empty:
        df_episodes = pd.concat([df_episodes, new_episodes], ignore_index=True)
        df_episodes.to_csv(EPISODES_CSV, index=False)
        logger.info("New episodes added and saved to CSV.")
    else:
        logger.info("No new episodes found.")

    return df_episodes

def download_episode(episode_number, episode_link):
    """Downloads an episode from a given URL."""
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(DOWNLOAD_FOLDER, f"episode_{episode_number}.mp3")

    try:
        response = requests.get(episode_link, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))

        with open(filepath, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True) as progress_bar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    progress_bar.update(len(chunk))

        logger.info(f"Downloaded: episode_{episode_number}.mp3")
        return "download_done"
    except Exception as e:
        logger.error(f"Error downloading {episode_link}: {e}")
        return "download_error"

def delete_download_folder():
    """Deletes the download folder and its contents."""
    if os.path.exists(DOWNLOAD_FOLDER):
        for filename in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
            try:
                os.remove(file_path)
                logger.info(f"Deleted: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting {file_path}: {e}")
        try:
            os.rmdir(DOWNLOAD_FOLDER)
            logger.info(f"Deleted folder: {DOWNLOAD_FOLDER}")
        except Exception as e:
            logger.error(f"Error deleting folder {DOWNLOAD_FOLDER}: {e}")
    else:
        logger.warning("Download folder does not exist.")

def process_episode(pipe, episode_number):
    """Processes an episode using the provided pipeline."""
    logger.info(f"Processing episode {episode_number}...")
    start_time = time.time()
    filepath = os.path.join(DOWNLOAD_FOLDER, f"episode_{episode_number}.mp3")

    try:
        prediction = pipe(filepath)["chunks"]
        end_time = time.time()
        logger.info(f"Time taken: {(end_time - start_time) / 60} minutes")

        os.makedirs(TEXT_FOLDER, exist_ok=True)
        with open(os.path.join(TEXT_FOLDER, f"episode_{episode_number}.txt"), "w", encoding="utf-8") as f:
            f.write(str(prediction))

        logger.info(f"Successfully processed episode {episode_number}.")
        return "done"
    except Exception as e:
        logger.error(f"Error processing episode {episode_number}: {e}")
        return "processing_error"

def prepare_whisper_model():
    """Prepares and returns the Whisper model pipeline."""
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        MODEL_ID, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained(MODEL_ID)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=30,
        batch_size=32,
        torch_dtype=torch_dtype,
        device=device,
        return_timestamps=True,
    )
    return pipe

if __name__ == "__main__":
    check_for_new_episodes = True
    df_episodes = load_episodes_df()

    if check_for_new_episodes:
        df_episodes = add_new_episodes(df_episodes)

    pipe = prepare_whisper_model()
    for index, row in df_episodes.iterrows():
        episode_link = row['link']
        episode_name = row['title']
        episode_state = row['state']
        episode_number = row['number']

        logger.info(f"Episode: {episode_name}")

        if episode_state == 'done':
            logger.info(f"Episode {episode_name} already processed.")
            continue

        if episode_state == 'skip':
            logger.info(f"Episode {episode_name} will be skipped.")
            continue

        state = download_episode(episode_number, episode_link)
        df_episodes.at[index, 'state'] = state
        if state == "download_error":
            df_episodes.at[index, 'state'] = 'skip'
        else:
            state = process_episode(pipe, episode_number)
            df_episodes.at[index, 'state'] = state

        df_episodes.to_csv(EPISODES_CSV, index=False)
        delete_download_folder()