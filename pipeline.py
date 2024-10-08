import asyncio
import json
import os
import boto3  # Import the boto3 library
from botocore.exceptions import ClientError
from datetime import datetime
from recall_api import process_video
from autoeditor.generator import generate_video
from monitor import get_top_videos
from reel_upload import upload_reel_from_s3
import random
import time

# Initialize the S3 client
s3_client = boto3.client('s3')

# This function uploads a file to the specified S3 bucket
async def upload_to_s3(file_path, bucket_name, s3_key):
    try:
        await asyncio.to_thread(s3_client.upload_file, file_path, bucket_name, s3_key)
        print(f"Successfully uploaded {file_path} to {bucket_name}/{s3_key}")
    except Exception as e:
        print(f"Failed to upload {file_path} to S3: {e}")

# This function splits the script into parts based on a character limit
# This is because Instagram Reel has a limit of 90 seconds
async def split_script(script, char_limit=1150, upper_limit=2100):
    def simple_split(arr, char_limit, upper_limit):
        parts = []
        current_part = []
        current_length = 0

        for i, element in enumerate(arr):
            element_length = len(element)

            # Check if the remaining elements (including current) are between char_limit and upper_limit
            remaining_length = sum(len(e) for e in arr[i:])
            if not current_part and char_limit < remaining_length <= upper_limit:
                middle_index = i + (len(arr[i:]) // 2)
                parts.append(arr[i:middle_index])
                parts.append(arr[middle_index:])
                return parts

            if current_length + element_length > char_limit and current_part:
                parts.append(current_part)
                current_part = []
                current_length = 0

            current_part.append(element)
            current_length += element_length

        if current_part:
            parts.append(current_part)

        return parts

    optimized_parts = simple_split(script, char_limit, upper_limit)

    # Print the different parts of the video script
    for i, part in enumerate(optimized_parts, 1):
        print(f"\nPart {i}:")
        print("\n".join(part))
        print(f"Character count: {sum(len(s) for s in part)}")

    return optimized_parts

async def generate_video_part(part_content, clip_generation_mode, part_number, selected_voice, bucket_name):
    temp_script_file = f"inputs/temp_script_part_{part_number}.json"
    os.makedirs("inputs", exist_ok=True)  # Ensure inputs directory exists
    os.makedirs("outputs", exist_ok=True)  # Ensure outputs directory exists
    with open(temp_script_file, 'w') as f:
        json.dump(part_content, f, indent=2)

    try:
        selected_voice = await asyncio.to_thread(
            generate_video,
            temp_script_file,
            clip_generation_mode,
            part_number=part_number,
            selected_voice=selected_voice
        )

        # Get the YouTube video ID from structured_summary.json
        with open("operation_data/structured_summary.json", "r") as f:
            structured_summary = json.load(f)
        video_url = structured_summary.get("video_url", "")
        video_id = video_url.split("v=")[-1]

        # Upload the generated video to S3
        video_file = f"outputs/reel_output_p{part_number}.mp4"
        s3_key = f"videos/{video_id}_p{part_number}.mp4"
        await upload_to_s3(video_file, bucket_name, s3_key)

        # Get the S3 URL for the uploaded video
        s3_video_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"

        # Upload the video to Instagram Reels
        upload_success = await asyncio.to_thread(upload_reel_from_s3, s3_video_url, part_number)
        if upload_success:
            print(f"Successfully uploaded Part {part_number} to Instagram Reels")

            # Add a random delay after successful upload
            delay = random.uniform(10, 600)  # Random delay between 10s to 10 minutes
            print(f"Waiting for {delay:.2f} seconds before processing the next video...")
            await asyncio.sleep(delay)
        else:
            print(f"Failed to upload Part {part_number} to Instagram Reels")

    except Exception as e:
        print(f"Error during video generation for Part {part_number}: {e}")
    finally:
        # Remove the temporary script file after uploading
        os.remove(temp_script_file)

    return selected_voice

# Main function to process a video URL and generate video(s)
async def process_and_generate_video(video_url, bucket_name, dynamo_table_name, clip_generation_mode="combine", test_video_only=False, min_char_count=800):
    # Create operation_data directory if it doesn't exist
    os.makedirs("operation_data", exist_ok=True)

    # Check if the video has already been processed
    if await check_video_history(dynamo_table_name, video_url):
        print(f"Video {video_url} has already been processed and uploaded. Skipping...")
        return

    # Process the video URL to generate an enhanced summary
    print(f"Processing video: {video_url}")
    enhanced_summary, processed_video_url = await process_video(video_url)

    if not enhanced_summary:
        print(f"Failed to process video: {video_url}")
        return

    print("Video processed successfully!")
    print("Enhanced summary:")
    print(json.dumps(enhanced_summary, indent=2))

    # Save the enhanced summary to the operation_data directory
    with open("operation_data/enhanced_summary.json", "w") as f:
        json.dump(enhanced_summary, f, indent=2)

    # Check if the enhanced summary is long enough
    total_chars = sum(len(s) for s in enhanced_summary['script'])
    if total_chars < min_char_count:
        print(f"Enhanced summary is too short ({total_chars} characters). Minimum required: {min_char_count}. Skipping video generation.")
        return

    # Store video information in DynamoDB
    await asyncio.to_thread(add_video_history, dynamo_table_name, processed_video_url, enhanced_summary)

    # Split the script into parts
    script_parts = await split_script(enhanced_summary['script'])

    selected_voice = None
    # Generate video for each part of the script
    for i, part_script in enumerate(script_parts, 1):
        # Add part number and continuation text
        part_script.insert(0, f"Part {i}.")

        if i < len(script_parts):
            part_script.append("To be continued in the next video")

        part_content = {
            "cover": enhanced_summary['cover'],
            "caption": enhanced_summary['caption'],
            "script": part_script
        }

        # Generate the video for this part and upload it to S3
        try:
            selected_voice = await generate_video_part(part_content, clip_generation_mode, i, selected_voice, bucket_name)
            print(f"Video generation for Part {i} completed successfully!")
        except Exception as e:
            print(f"Error during video generation for Part {i}: {e}")

    print("All video parts generated and uploaded to S3 successfully!")


def add_video_history(table_name, video_url, enhanced_summary):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    try:
        table.put_item(
            Item={
                'video_url': video_url,
                'processed_at': datetime.now().isoformat(),
                'enhanced_summary': json.dumps(enhanced_summary)
            }
        )
        print(f"Added video history for: {video_url}")
    except ClientError as e:
        print(f"Error adding video history to DynamoDB: {e}")

async def check_video_history(table_name, video_url):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    try:
        # Use a query instead of get_item
        response = await asyncio.to_thread(
            table.query,
            KeyConditionExpression=boto3.dynamodb.conditions.Key('video_url').eq(video_url)
        )
        if response['Items']:
            latest_item = max(response['Items'], key=lambda x: x['processed_at'])
            print(f"Found existing entry for video: {video_url}")
            print(f"Processed at: {latest_item['processed_at']}")
            return True
        return False
    except ClientError as e:
        print(f"Error checking video history in DynamoDB: {e}")
        return False

async def get_channel_ids(table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = await asyncio.to_thread(table.scan)
    return [item['channel_id'] for item in response.get('Items', [])]

# Main entry point of the script
async def main():
    channel_table_name = "YouTubeChannelMonitor"
    video_history_table_name = "VideoProcessingHistory"
    channel_ids = await get_channel_ids(channel_table_name)

    # Set the hours_ago parameter
    hours_ago = 48  # You can change this value as needed

    # Set the minimum character count for video generation
    min_char_count = 800  # You can adjust this value as needed

    # Set the maximum number of videos to process
    max_videos = 5  # You can adjust this value as needed

    # Get top video URLs from monitored channels
    top_video_urls = await get_top_videos(channel_ids, hours_ago, max_videos)

    # Process each video URL
    for url in top_video_urls:
        try:
            await process_and_generate_video(url, "recall-bot-ig-reel", video_history_table_name, test_video_only=False, min_char_count=min_char_count)
        except Exception as e:
            print(f"Error processing video {url}: {e}")
            import traceback
            traceback.print_exc()  # This will print the full stack trace



if __name__ == "__main__":
    asyncio.run(main())
