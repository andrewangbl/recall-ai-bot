from tiktokvoice import tts, get_duration, merge_audio_files
from srt import gen_srt_file
from editor import VideoEditor
import subprocess
import os
import re

def read_text_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def format_duration(duration):
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    milliseconds = int((duration - int(duration)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

if __name__ == "__main__":
    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("ffmpeg is not installed. Please install ffmpeg to continue.")
        exit(1)

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

    # Get the text file from the inputs folder
    script_file = input("Enter the name of the script file (with extension) in the inputs folder:\n")
    script_file_path = os.path.join("inputs", script_file)

    if not os.path.exists(script_file_path):
        print(f"Script file '{script_file}' not found in the inputs folder.")
        exit(1)

    # Read the content from the script file
    content = read_text_file(script_file_path)
    script_lines = content.split('\n')

    # Print the content details
    print("Content from script file:")
    for line in script_lines:
        print(line)

    # Ask if the user wants to proceed
    proceed = input("Do you want to proceed with video creation? (y/n)\n")
    if proceed.lower() != "y":
        print("Exiting")
        exit(0)

    # Create the audio files and SRT for each sentence
    audio_segments = []
    srt_content = ""
    current_time = 0.0
    index = 1

    for i, paragraph in enumerate(script_lines):
        if not paragraph.strip():  # Skip empty lines
            continue

        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        for sentence in sentences:
            filename = f"outputs/temp_audio_{i}_{index}.mp3"
            try:
                tts(sentence, "en_us_001", filename, 1.15)
                duration = get_duration(filename)
                audio_segments.append((sentence, duration))

                start_time = format_duration(current_time)
                current_time += duration
                end_time = format_duration(current_time)

                srt_content += f"{index}\n{start_time} --> {end_time}\n{sentence.strip()}\n\n"
                current_time += 0.1  # Add a small delay between sentences
                index += 1
            except Exception as e:
                print(f"Error creating audio for sentence {i}: {e}")
                continue

    print("Created audio files for script")

    # Write SRT content to file
    srt_path = f"inputs/output.srt"
    with open(srt_path, "w") as f:
        f.write(srt_content)

    # Merge the audio files into one
    wav_path = f"inputs/output.wav"
    try:
        total_duration = merge_audio_files(wav_path, 0.1)
        print("Merged audio duration:", total_duration, "seconds")
    except Exception as e:
        print(f"Error merging audio files: {e}")
        exit(1)

    # Create the video
    try:
        video_editor = VideoEditor(total_duration, srt_path, wav_path, False)
        video_editor.start_render(f"outputs/output.mp4")
    except Exception as e:
        print(f"Error rendering video: {e}")
        exit(1)
