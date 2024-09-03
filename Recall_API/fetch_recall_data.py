import requests
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# API endpoint
url = "https://apollo.getrecall.ai/scraper/"

# YouTube video URL
video_url = "https://www.youtube.com/watch?v=LEx2_zLobrM"

# Your API key
api_key = os.getenv('RECALL_API_SECRET')

# Headers
headers = {
    "Authorization": f"Bearer {api_key}"
}

# Parameters
params = {
    "url": video_url
}

# Make the GET request
try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raises an HTTPError for bad responses

    raw_data = response.json()

    # Output to a file
    output_file = "raw_recall_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    print(f"Raw data saved to {output_file}")

except requests.exceptions.RequestException as e:
    print(f"Error making request: {e}")
except json.JSONDecodeError:
    print("Error decoding JSON response")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
