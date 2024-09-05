import os
from dotenv import load_dotenv
import requests
import time
import json

# Load environment variables
load_dotenv()

graph_url = 'https://graph.facebook.com/v18.0/'

def post_reel(caption, video_url, access_token, instagram_account_id):
    # Creating a container for the Reel
    url = f"{graph_url}{instagram_account_id}/media"
    params = {
        'access_token': access_token,
        'caption': caption,
        'media_type': 'REELS',
        'share_to_feed': 'true',
        'video_url': video_url
    }
    response = requests.post(url, params=params)
    print("\nResponse:", response.content)
    return response.json()

def status_of_upload(ig_container_id, access_token):
    # Checking upload status
    # make a GET request to check the status of the upload
    url = f"{graph_url}{ig_container_id}"
    params = {
        'access_token': access_token,
        'fields': 'status_code'
    }
    response = requests.get(url, params=params)
    return response.json()

def publish_container(creation_id, access_token, instagram_account_id):
    # Publishing the reel
    # making a POST request to publish the reel
    url = f"{graph_url}{instagram_account_id}/media_publish"
    params = {
        'access_token': access_token,
        'creation_id': creation_id
    }
    response = requests.post(url, params=params)
    return response.json()

def upload_and_publish_reel(video_url, caption, access_token, instagram_account_id):
    # Step 1: Create a container for the Reel
    container_response = post_reel(caption, video_url, access_token, instagram_account_id)
    if 'id' not in container_response:
        print("Error creating container:", container_response)
        return False

    container_id = container_response['id']
    print(f"Container created with ID: {container_id}")

    # Step 2: Check the upload status
    while True:
        status = status_of_upload(container_id, access_token)
        if status.get('status_code') == 'FINISHED':
            print("Container Upload finished successfully")
            break
        elif status.get('status_code') in ['ERROR', 'EXPIRED']:
            print("Error in upload:", status)
            return False
        print("Upload in progress, waiting...")
        time.sleep(5)  # Wait for 5 seconds before checking again

    # Step 3: Publish the container
    publish_response = publish_container(container_id, access_token, instagram_account_id)
    if 'id' in publish_response:
        print(f"Reel published successfully with ID: {publish_response['id']}")
        return True
    else:
        print("Error publishing reel:", publish_response)
        return False

def upload_reel_from_s3(s3_video_url, part_number):
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    instagram_account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')

    if access_token is None or instagram_account_id is None:
        print("Error: INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID not found in .env file")
        return False

    # Load the enhanced summary
    with open("operation_data/enhanced_summary.json", "r") as f:
        enhanced_summary = json.load(f)

    # Load the structured summary to get the video title
    with open("operation_data/structured_summary.json", "r") as f:
        structured_summary = json.load(f)

    # Get the video title
    video_title = structured_summary.get("title", "Untitled Video")

    # Prepare the caption
    caption = f'Part {part_number}: "{video_title}" summary\n\n'
    caption += enhanced_summary['caption']

    # Upload and publish the reel
    return upload_and_publish_reel(s3_video_url, caption, access_token, instagram_account_id)
