import os
import re
import json
from .tts import tts, get_duration, merge_audio_files, get_random_voice
from .srt import gen_srt_file
from .editor import VideoEditor

def generate_video(input_json_path, clip_generation_mode="normal", part_number=1, selected_voice=None):
    # Read the content from the JSON file
    with open(input_json_path, 'r') as f:
        part_content = json.load(f)

    script_lines = part_content['script']
    cover = part_content['cover']
    caption = part_content['caption']

    # Process the script lines to generate audio and video
    audio_segments = []
    srt_content = ""
    current_time = 0.0
    index = 1

    # Select a random voice for the entire video if not provided
    if selected_voice is None:
        selected_voice = get_random_voice()
    print(f"Selected voice: {selected_voice}")

    def split_into_sentences(text):
        # Handle common abbreviations
        text = re.sub(r'(?<=[A-Z])\.(?=[A-Z]\.)', '<PERIOD>', text)
        text = re.sub(r'(?<=Dr)\.', '<PERIOD>', text)
        text = re.sub(r'(?<=Mr)\.', '<PERIOD>', text)
        text = re.sub(r'(?<=Mrs)\.', '<PERIOD>', text)
        text = re.sub(r'(?<=Ms)\.', '<PERIOD>', text)
        # Add more abbreviations as needed

        # Split sentences
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

        # Restore periods in abbreviations
        sentences = [s.replace('<PERIOD>', '.') for s in sentences]

        return [s.strip() for s in sentences if s.strip()]

    for paragraph in script_lines:
        sentences = split_into_sentences(paragraph)
        for sentence in sentences:
            filename = f"outputs/temp_audio_{index}.mp3"
            try:
                tts(sentence, selected_voice, filename, 1.25)
                duration = get_duration(filename)

                audio_segments.append((sentence, duration))

                start_time = format_duration(current_time)
                current_time += duration
                end_time = format_duration(current_time)

                srt_content += f"{index}\n{start_time} --> {end_time}\n{sentence.strip()}\n\n"
                current_time += 0.1  # Add a small delay between sentences
                index += 1
            except Exception as e:
                print(f"Error creating audio for sentence {index}: {e}")
                continue

    print("Created audio files for script")

    # Write SRT content to file
    srt_path = f"operation_data/output.srt"
    with open(srt_path, "w") as f:
        f.write(srt_content)

    # Merge the audio files into one
    wav_path = f"operation_data/output.wav"
    try:
        total_duration = merge_audio_files(wav_path, 0.1)
        print("Merged audio duration:", total_duration, "seconds")
    except Exception as e:
        print(f"Error merging audio files: {e}")
        return

    # Modify the output filename
    output_filename = f"outputs/reel_output_p{part_number}.mp4"

    # Create the video
    try:
        video_editor = VideoEditor(total_duration, srt_path, wav_path, False, clip_generation_mode=clip_generation_mode, part_number=part_number)
        video_editor.cover_img_url = cover
        video_editor.start_render(output_filename)
    except Exception as e:
        print(f"Error rendering video: {e}")
        return

    print("Video generation completed successfully!")
    return selected_voice

def format_duration(duration):
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    milliseconds = int((duration - int(duration)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
