from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

"""
1. It reads the channel names from monitor_list.txt.
2. For each channel name, it fetches the channel ID.
3. It then searches for videos from each channel published in the last 48 hours.
4. It filters the videos based on duration (between 10 minutes and 5 hours by default).
5. Finally, it selects the video with the highest view count and output its URL.
"""

# Load environment variables from .env file
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

def get_latest_videos(channel_id, published_after, min_duration=600, max_duration=18000):
    try:
        search_response = youtube.search().list(
            channelId=channel_id,
            type="video",
            order="date",
            part="id,snippet",
            maxResults=50,
            publishedAfter=published_after.isoformat() + "Z"
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if not video_ids:
            return []

        videos_response = youtube.videos().list(
            part="contentDetails,statistics",
            id=','.join(video_ids)
        ).execute()

        filtered_videos = []
        for video in videos_response.get('items', []):
            try:
                duration = parse_duration(video['contentDetails']['duration'])
                if min_duration <= duration <= max_duration:
                    filtered_videos.append({
                        'id': video['id'],
                        'title': next(item['snippet']['title'] for item in search_response['items'] if item['id']['videoId'] == video['id']),
                        'views': int(video['statistics']['viewCount']),
                        'likes': int(video['statistics'].get('likeCount', 0)),
                        'duration': duration
                    })
            except (KeyError, ValueError) as e:
                print(f"Error processing video {video.get('id', 'unknown')}: {e}")
                continue

        return filtered_videos

    except Exception as e:
        print(f"Error fetching videos for channel {channel_id}: {e}")
        return []

def parse_duration(duration_str):
    hours = minutes = seconds = 0
    duration_str = duration_str.replace('PT', '')
    if 'H' in duration_str:
        hours, duration_str = duration_str.split('H')
        hours = int(hours)
    if 'M' in duration_str:
        minutes, duration_str = duration_str.split('M')
        minutes = int(minutes)
    if 'S' in duration_str:
        seconds = int(duration_str.replace('S', ''))
    return hours * 3600 + minutes * 60 + seconds

def find_best_video(channel_names, hours_ago=48, min_duration=600, max_duration=18000):
    channel_ids = {}
    for name in channel_names:
        channel_id = get_channel_id(name)
        if channel_id:
            channel_ids[name] = channel_id
            print(f"Channel: {name}, ID: {channel_id}")
        else:
            print(f"Could not find channel ID for: {name}")

    published_after = datetime.utcnow() - timedelta(hours=hours_ago)
    all_videos = []

    for channel_name, channel_id in channel_ids.items():
        videos = get_latest_videos(channel_id, published_after, min_duration, max_duration)
        all_videos.extend(videos)

    if not all_videos:
        print("No videos found matching the criteria.")
        return None

    best_video = max(all_videos, key=lambda x: x['views'])
    return f"https://www.youtube.com/watch?v={best_video['id']}"

# Read channel names from monitor_list.txt
with open('monitor/monitor_list.txt', 'r') as file:
    channel_names = [line.split(',')[0].replace('Channel: ', '').strip() for line in file if line.strip()]

# Find the best video
best_video_url = find_best_video(channel_names, hours_ago=48, min_duration=600, max_duration=18000)

if best_video_url:
    print(f"Best video URL: {best_video_url}")
else:
    print("No suitable videos found.")
