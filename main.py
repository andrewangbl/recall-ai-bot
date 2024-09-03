from autoeditor.generator import generate_video
import os

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


    script_file_path = "inputs/blackwhole.txt"
    clip_generation_mode = "combine"

    # Generate the video
    generate_video(script_file_path, clip_generation_mode)
