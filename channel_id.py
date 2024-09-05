from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("YOUTUBE_API_KEY")

# Create a YouTube API client
youtube = build('youtube', 'v3', developerKey=api_key)

def get_channel_id(channel_name):
    try:
        search_response = youtube.search().list(
            q=channel_name,
            type='channel',
            part='id',
            maxResults=1
        ).execute()

        if 'items' in search_response and search_response['items']:
            return search_response['items'][0]['id']['channelId']
        else:
            return None
    except Exception as e:
        print(f"Error fetching channel ID for {channel_name}: {e}")
        return None

# Read channel names from monitor_list.txt
with open('monitor/monitor_list.txt', 'r') as file:
    channel_names = [line.strip() for line in file if line.strip()]

# Get channel IDs
channel_ids = {}
for name in channel_names:
    channel_id = get_channel_id(name)
    if channel_id:
        channel_ids[name] = channel_id
        print(f"Channel: {name}, ID: {channel_id}")
    else:
        print(f"Could not find channel ID for: {name}")

# You can now use the channel_ids dictionary for further processing
