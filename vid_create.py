from autoeditor.generator import generate_video
import os
import json

def split_script(script, char_limit=1300):
    parts = []
    current_part = []
    current_char_count = 0

    for sentence in script:
        if len(sentence) > char_limit:
            raise ValueError(f"A single element in the script exceeds {char_limit} characters.")

        if current_char_count + len(sentence) > char_limit:
            if current_part:
                parts.append(current_part)
                current_part = []
                current_char_count = 0
            else:
                # If we can't fit even one sentence, we need to split it
                mid_point = len(sentence) // 2
                parts.append([sentence[:mid_point]])
                current_part = [sentence[mid_point:]]
                current_char_count = len(sentence) - mid_point
                continue

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

if __name__ == "__main__":
    # Check if the outputs folder exists
    if not os.path.exists("outputs"):
        os.mkdir("outputs")
        print("Created outputs folder\n - This is where final videos will be saved.")
    # Check if the inputs folder exists
    if not os.path.exists("inputs"):
        os.mkdir("inputs")
        print("Created inputs folder\n - This is where input video files will need to be stored\n - The srt and wav files will also be stored here.")

    # Check if any mp4 files are present in the inputs folder
    if len([i for i in os.listdir("inputs") if i.endswith(".mp4")]) == 0:
        print("No input video files found in the inputs folder. Add your input video files to this folder.")
        exit(1)

    script_file_path = "enhanced_summary.json"

    # Check if the enhanced_summary.json file exists
    if not os.path.exists(script_file_path):
        print(f"Error: {script_file_path} not found. Please make sure the file exists in the project root directory.")
        exit(1)

    clip_generation_mode = "combine"

    # Load the enhanced summary
    with open(script_file_path, 'r') as f:
        enhanced_summary = json.load(f)

    # Split the script into parts
    script_parts = split_script(enhanced_summary['script'])

    # Generate videos for each part
    selected_voice = None
    for i, part_script in enumerate(script_parts, 1):
        # Add part number and continuation text
        if i == 1:
            part_script.insert(0, f"Part {i}")
        else:
            part_script.insert(0, f"Part {i}. Continued from part {i-1}")

        # Add "to be continued" for all parts except the last one
        if i < len(script_parts):
            part_script.append("To be continued in the next video")

        part_content = {
            "cover": enhanced_summary['cover'],
            "caption": enhanced_summary['caption'],
            "script": part_script
        }

        # Save the part script to a temporary file
        temp_script_file = f"inputs/temp_script_part_{i}.json"
        with open(temp_script_file, 'w') as f:
            json.dump(part_content, f, indent=2)

        # Generate the video for this part
        try:
            selected_voice = generate_video(temp_script_file, clip_generation_mode, part_number=i, selected_voice=selected_voice)
            print(f"Video generation for Part {i} completed successfully!")
        except Exception as e:
            print(f"Error during video generation for Part {i}: {e}")

        # Remove the temporary script file
        os.remove(temp_script_file)

    print("All parts generated successfully!")
