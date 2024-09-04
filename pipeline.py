import asyncio
import json
import os
from recall_api import process_video
from autoeditor.generator import generate_video

# This function splits the script into parts based on a character limit
# This is because Instagram Reel has a limit of 90 seconds
async def split_script(script, char_limit=1300):
    # This function returns a list of script parts, and each part will be made into a video
    parts = []
    current_part = []
    current_char_count = 0

    for sentence in script:
        if current_char_count + len(sentence) > char_limit:
            parts.append(current_part)
            current_part = [sentence]
            current_char_count = len(sentence)
        else:
            current_part.append(sentence)
            current_char_count += len(sentence)

    if current_part:
        remaining_chars = sum(len(s) for s in current_part)
        if char_limit < remaining_chars < 2 * char_limit:
            total_chars = remaining_chars
            mid_char_count = total_chars // 2
            current_count = 0
            split_index = 0

            for i, sentence in enumerate(current_part):
                current_count += len(sentence)
                if current_count > mid_char_count:
                    split_index = i
                    break

            parts.append(current_part[:split_index])
            parts.append(current_part[split_index:])
        else:
            parts.append(current_part)

    return parts

# This function generates a video for a single part of the script
async def generate_video_part(part_content, clip_generation_mode, part_number, selected_voice):
    # This function returns the selected voice for consistency across parts
    temp_script_file = f"inputs/temp_script_part_{part_number}.json"
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
        print(f"Video generation for Part {part_number} completed successfully!")
    except Exception as e:
        print(f"Error during video generation for Part {part_number}: {e}")
    finally:
        # Remove the temporary script file
        await asyncio.to_thread(os.remove, temp_script_file)

    return selected_voice

# Main function to process a video URL and generate video(s)
async def process_and_generate_video(video_url, clip_generation_mode="combine", test_video_only=False):
    # If test_video_only is True, use a pre-existing enhanced summary
    if test_video_only:
        # Load the enhanced summary from a JSON file in the root directory
        with open("enhanced_summary.json", "r") as f:
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

        # Note: The enhanced_summary.json file is created in the root directory by the process_video function

    # Split the script into parts
    script_parts = await split_script(enhanced_summary['script'])

    selected_voice = None
    # Generate video for each part of the script
    for i, part_script in enumerate(script_parts, 1):
        # Add part number and continuation text
        if i == 1:
            part_script.insert(0, f"Part {i}")
        else:
            part_script.insert(0, f"Part {i}. Continued from part {i-1}")

        if i < len(script_parts):
            part_script.append("To be continued in the next video")

        part_content = {
            "cover": enhanced_summary['cover'],
            "caption": enhanced_summary['caption'],
            "script": part_script
        }

        # Create a temporary JSON file for each part in the inputs directory
        temp_script_file = f"inputs/temp_script_part_{i}.json"
        with open(temp_script_file, 'w') as f:
            json.dump(part_content, f, indent=2)

        try:
            # Generate the video for this part
            # The output video file will be saved in the outputs directory as reel_output_p{i}.mp4
            selected_voice = generate_video(
                temp_script_file,
                clip_generation_mode,
                part_number=i,
                selected_voice=selected_voice
            )
            print(f"Video generation for Part {i} completed successfully!")
        except Exception as e:
            print(f"Error during video generation for Part {i}: {e}")
        finally:
            # Remove the temporary script file
            os.remove(temp_script_file)

    print("All video parts generated successfully!")

# Main entry point of the script
async def main():
    video_url = "https://www.youtube.com/watch?v=arC9jtPLz7s"  # Example video URL
    await process_and_generate_video(video_url)

if __name__ == "__main__":
    asyncio.run(main())

# Output files generated by this script:
# 1. enhanced_summary.json (in the root directory) - contains the enhanced summary of the video
# 2. reel_output_p{i}.mp4 (in the outputs directory) - the generated video file(s), where {i} is the part number
# 3. Temporary files in the inputs directory (deleted after use):
#    - temp_script_part_{i}.json - temporary script files for each part
#    - output.srt - subtitle file (created and used by generate_video function)
#    - output.wav - audio file (created and used by generate_video function)
# Note: The inputs and outputs directories are created if they don't exist
