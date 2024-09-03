import os
import re
from .tts import tts, get_duration, merge_audio_files, get_random_voice
from .srt import gen_srt_file
from .editor import VideoEditor

def generate_video(input_text_path, clip_generation_mode="normal"):
    # Read the content from the script file
    with open(input_text_path, 'r') as file:
        content = file.read()
    script_lines = content.split('\n')

    # Create the audio files and SRT for each sentence
    audio_segments = []
    srt_content = ""
    current_time = 0.0
    index = 1

    # Select a random voice for the entire video
    selected_voice = get_random_voice()
    print(f"Selected voice: {selected_voice}")

    for i, paragraph in enumerate(script_lines):
        if not paragraph.strip():  # Skip empty lines
            continue

        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        for sentence in sentences:
            filename = f"outputs/temp_audio_{i}_{index}.mp3"
            try:
                tts(sentence, selected_voice, filename, 1.15)
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
        return

    # Create the video
    try:
        video_editor = VideoEditor(total_duration, srt_path, wav_path, False, clip_generation_mode=clip_generation_mode)
        video_editor.start_render(f"outputs/reel_output.mp4")
    except Exception as e:
        print(f"Error rendering video: {e}")
        return

    print("Video generation completed successfully!")

def format_duration(duration):
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    milliseconds = int((duration - int(duration)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
