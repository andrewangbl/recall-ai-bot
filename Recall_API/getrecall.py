import requests
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_recall_data(video_url):
    url = "https://apollo.getrecall.ai/scraper/"
    api_key = os.getenv('RECALL_API_SECRET')

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    params = {
        "url": video_url
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Recall API: {e}")
        return None
