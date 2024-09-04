import requests
from dotenv import load_dotenv
import os
import json
import re

# Load environment variables
load_dotenv()

# API endpoint
url = "https://apollo.getrecall.ai/scraper/"

# YouTube video URL
video_url = "https://www.youtube.com/watch?v=LtSx6nWN-YU"

# Your API key
api_key = os.getenv('RECALL_API_SECRET')

# Headers
headers = {
    "Authorization": f"Bearer {api_key}"  # Add 'Bearer ' prefix
}

# Parameters
params = {
    "url": video_url
}

def parse_recall_summary(summary):
    structured_summary = {
        "title": summary.get("name", ""),
        "cover": "",
        "tags": [],
        "summary": {}
    }

    # Extract cover image
    editor_blocks = summary.get("editorBlocks", [])
    for block in editor_blocks:
        for child in block.get("children", []):
            if child.get("type") == "image":
                structured_summary["cover"] = child.get("urlOriginal", "")
                break
        if structured_summary["cover"]:
            break

    # Extract tags (using 'links' as tags)
    links = summary.get("links", [])
    structured_summary["tags"] = [link.get("name", "") for link in links]

    # Parse description content
    description = summary.get("description", "")
    lines = description.split(". ")
    current_section = "Introduction"
    structured_summary["summary"][current_section] = []

    for line in lines:
        timestamp_match = re.search(r'\[([\d.]+)\]', line)
        if timestamp_match:
            timestamp = timestamp_match.group(1)
            text = re.sub(r'\[[\d.]+\]\s*', '', line).strip()

            # Check if this is a new section
            if text.endswith(":"):
                current_section = text[:-1]
                structured_summary["summary"][current_section] = []
            else:
                url = f"https://www.youtube.com/watch?v=JHDgN1FfAd8&t={int(float(timestamp))}s"
                structured_summary["summary"][current_section].append({
                    "text": text,
                    "timestamp": timestamp,
                    "url": url
                })

    return structured_summary

# Make the GET request
try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raises an HTTPError for bad responses

    summary = response.json()
    structured_summary = parse_recall_summary(summary, video_url)

    # Output to a file
    output_file = "structured_summary.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structured_summary, f, ensure_ascii=False, indent=2)

    print(f"Structured summary saved to {output_file}")

except requests.exceptions.RequestException as e:
    print(f"Error making request: {e}")
except json.JSONDecodeError:
    print("Error decoding JSON response")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
