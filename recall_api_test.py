import asyncio
from recall_api import process_video

async def main():
    video_url = "https://www.youtube.com/watch?v=JHDgN1FfAd8"  # Example video URL

    print("Processing video...")
    enhanced_summary = await process_video(video_url)

    if enhanced_summary:
        print("Video processed successfully!")
        print("Enhanced summary:")
        print(enhanced_summary)
    else:
        print("Failed to process video.")

if __name__ == "__main__":
    asyncio.run(main())
