import feedparser
from datetime import datetime, timedelta
import aiohttp
import asyncio
import re

async def get_latest_videos_rss(channel_id, hours_ago=24):
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(rss_url) as response:
            feed_content = await response.text()

    feed = feedparser.parse(feed_content)

    current_time = datetime.utcnow()
    time_threshold = current_time - timedelta(hours=hours_ago)

    videos = []
    for entry in feed.entries:
        published_time = datetime(*entry.published_parsed[:6])
        if published_time > time_threshold:
            video_id = entry.yt_videoid
            videos.append({
                'id': video_id,
                'title': entry.title,
                'published_at': published_time,
                'url': f"https://www.youtube.com/watch?v={video_id}"
            })

    return videos

async def get_video_details(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()

    view_count_match = re.search(r'"viewCount":"(\d+)"', html_content)
    view_count = int(view_count_match.group(1)) if view_count_match else 0

    return {'views': view_count}

async def find_top_video(channel_id):
    videos = await get_latest_videos_rss(channel_id)
    if not videos:
        return None

    video_details = await asyncio.gather(*[get_video_details(video['id']) for video in videos])
    for video, details in zip(videos, video_details):
        video.update(details)

    top_video = max(videos, key=lambda x: x['views'])
    return top_video['url']

async def get_top_videos(channel_ids):
    top_videos = await asyncio.gather(*[find_top_video(channel_id) for channel_id in channel_ids])
    return [video for video in top_videos if video]

async def main():
    with open('monitor/monitor_list.txt', 'r') as file:
        channel_ids = [line.split(',')[1].strip() for line in file if line.strip()]

    top_video_urls = await get_top_videos(channel_ids)
    return top_video_urls

if __name__ == "__main__":
    top_videos = asyncio.run(main())
    for url in top_videos:
        print(url)
