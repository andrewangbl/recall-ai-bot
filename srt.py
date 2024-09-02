# Function to generate an SRT file from subtitles
def gen_srt_file(subtitles: list, file_path: str, delay: float = 0.1):
    """
    Generate an SRT file from a list of subtitles.

    Args:
        subtitles (list): A list of (text, duration) pairs representing the subtitles.
        file_path (str): The file path where the SRT file will be saved.
        delay (float, optional): The delay in seconds to be added after each subtitle. Defaults to 0.1.
    """
    import re

    def format_duration(duration):
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        milliseconds = int((duration - int(duration)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def split_into_sentences(text):
        # This regex splits on .!? followed by space or "
        return re.split(r'([.!?][\s"])', text)

    srt_content = ""
    current_time = 0.0
    index = 1

    for text, duration in subtitles:
        # Join the split parts back together
        sentences = [''.join(sentence).strip() for sentence in zip(split_into_sentences(text)[::2], split_into_sentences(text)[1::2] + [''])]
        sentences = [s for s in sentences if s]  # Remove empty strings

        char_count = sum(len(sentence) for sentence in sentences)

        for sentence in sentences:
            if not sentence.strip():
                continue

            sentence_duration = duration * (len(sentence) / char_count)

            start_time = format_duration(current_time)
            current_time += sentence_duration
            end_time = format_duration(current_time)

            srt_content += f"{index}\n{start_time} --> {end_time}\n{sentence.strip()}\n\n"
            current_time += delay
            index += 1

    with open(file_path, "w") as f:
        f.write(srt_content)
    print(f"SRT file successfully generated at '{file_path}'")
