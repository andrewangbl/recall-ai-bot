import asyncio
import json
import os
import re
import glob
import boto3  # Import the boto3 library
from recall_api import process_video
from autoeditor.generator import generate_video
from monitor import get_top_videos
from reel_upload import upload_reel_from_s3

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
async def split_script(script, char_limit=1100, upper_limit=2000):
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
        else:
            print(f"Failed to upload Part {part_number} to Instagram Reels")

    except Exception as e:
        print(f"Error during video generation for Part {part_number}: {e}")
    finally:
        # Remove the temporary script file after uploading
        os.remove(temp_script_file)

    return selected_voice

# Main function to process a video URL and generate video(s)
async def process_and_generate_video(video_url, bucket_name, clip_generation_mode="combine", test_video_only=True):
    # Create operation_data directory if it doesn't exist
    os.makedirs("operation_data", exist_ok=True)

    # If test_video_only is True, use a pre-existing enhanced summary
    if test_video_only:
        # Load the enhanced summary from a JSON file in the operation_data directory
        with open("operation_data/enhanced_summary.json", "r") as f:
            enhanced_summary = json.load(f)
    else:
        # Process the video URL to generate an enhanced summary
        print("Processing video...")
        enhanced_summary = await process_video(video_url)

        if not enhanced_summary:
            print("Failed to process video.")
            return

        print("Video processed successfully!")
        print("Enhanced summary:")
        print(json.dumps(enhanced_summary, indent=2))

        # Save the enhanced summary to the operation_data directory
        with open("operation_data/enhanced_summary.json", "w") as f:
            json.dump(enhanced_summary, f, indent=2)

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

# Main entry point of the script
async def main():
    # Get channel IDs from the monitor list
    channel_ids = []
    with open('monitor/monitor_list.txt', 'r') as file:
        channel_ids = [line.split(',')[1].strip() for line in file if line.strip()]

    # Set the hours_ago parameter
    hours_ago = 24  # You can change this value as needed

    # Get top video URLs from monitored channels
    top_video_urls = await get_top_videos(channel_ids, hours_ago)

    # Process each video URL
    for url in top_video_urls:
        try:
            await process_and_generate_video(url, "recall-bot-ig-reel", test_video_only=False)
        except Exception as e:
            print(f"Error processing video {url}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
