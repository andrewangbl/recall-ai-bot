import asyncio
from .getrecall import fetch_recall_data
from .parser import parse_recall_summary
from .gpt_summary import generate_enhanced_summary
import json
import os

async def process_video(video_url):
    # Create operation_data directory if it doesn't exist
    os.makedirs("operation_data", exist_ok=True)

    # Step 1: Fetch data from Recall API
    raw_data = await asyncio.to_thread(fetch_recall_data, video_url)
    if not raw_data:
        return None

    # Step 2: Parse the raw data into structured summary
    structured_summary = parse_recall_summary(raw_data, video_url)

    # Save structured summary
    with open("operation_data/structured_summary.json", "w") as f:
        json.dump(structured_summary, f, indent=2)

    # Step 3: Generate enhanced summary using GPT
    enhanced_summary = await asyncio.to_thread(generate_enhanced_summary, structured_summary)

    # Save enhanced summary
    with open("operation_data/enhanced_summary.json", "w") as f:
        json.dump(enhanced_summary, f, indent=2)

    return enhanced_summary

# Usage
if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=LEx2_zLobrM"  # Replace with your video URL
    asyncio.run(process_video(video_url))
