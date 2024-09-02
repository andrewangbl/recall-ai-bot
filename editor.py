from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import random
import math
import os


class VideoEditor:
    def __init__(self, clip_duration, srt_path, wav_path, animate_text=True):
        """
        Initialize the Editor object.

        Args:
            reddit_id (str): The ID of the Reddit post.
            clip_duration (int): The duration of the video clip in seconds.
            srt_path (str): The path to the SRT file.
            wav_path (str): The path to the WAV file.

        Attributes:
            reddit_id (str): The ID of the Reddit post.
            clip_duration (int): The duration of the video clip in seconds.
            srt_path (str): The path to the SRT file.
            wav_path (str): The path to the WAV file.
            bg_path (list): A list of background video paths.
            background_video (VideoFileClip): The background video clip.
        """
        # The Y coordinate of the text.
        self.y_cord = 1080
        # Whether to animate the text or not.
        self.animate_text = animate_text
        # The intended duration of the video clip in seconds.
        self.clip_duration = clip_duration
        # The path to the WAV and SRT file.
        self.srt_path = srt_path
        self.wav_path = wav_path

        # A list of background videos
        self.bg_path = [
            f for f in os.listdir("inputs") if f.endswith('.mp4')]
        # Randomly select a background video to use later
        self.bg_path = random.choice(self.bg_path)
        self.background_video = VideoFileClip(
            os.path.join("inputs", self.bg_path))

        # Default vertical position (70% from top)
        self.y_position = 0.5

    def __text_generator(self, txt):
        """
        Generate a TextClip object with the specified text and style.

        Parameters:
        txt (str): The text to be displayed.

        Returns:
        TextClip: A TextClip object with the specified text and style.
        """
        # Determine font size based on text length
        if len(txt) > 100:
            fontsize = 24
        elif len(txt) > 50:
            fontsize = 28
        else:
            fontsize = 32

        return TextClip(
            txt,
            font='Arial-Bold', fontsize=fontsize,
            stroke_color='black', stroke_width=0.75,
            color='white', method='caption', size=(350, None),
            align='center'
        )

    def __simple_slideup(self, t):
        """
        Slide the text up the screen until it reaches the center.

        Args:
            t: The time parameter for the animation.

        Returns:
            A tuple containing the horizontal alignment ('center') and the updated vertical position of the text.
        """
        if self.y_cord > 500:
            self.y_cord -= 130
        return 'center', self.y_cord

    def set_subtitle_position(self, position):
        """
        Set the vertical position of subtitles.
        :param position: Float between 0 and 1, where 0 is top and 1 is bottom.
        """
        self.y_position = position

    def start_render(self, output_path="outputs/output.mp4"):
        """
        Starts the rendering process by creating a video clip with subtitles.

        Args:
            output_path (str): The path to save the rendered video file. Default is "outputs/output.mp4".

        Returns:
            None
        """
        print("Rendering video...")
        # The maximum time to start the video clip from. (Otherwise the clip will cut to black)
        self.upperlimit_time = (
            self.background_video.duration -
            math.ceil(10 * self.clip_duration) / 10
        )

        # Randomly select a start time for the video clip
        self.start_time = random.randint(0, math.floor(self.upperlimit_time))
        print(
            f"Start time: {self.start_time} seconds |",
            f"End time: {self.start_time + self.clip_duration} seconds"
        )

        # Clip the video from the start time to the desired endtime
        self.rendered_video = self.background_video.subclip(
            self.start_time,
            self.start_time + self.clip_duration
        )
        # Set the FPS to 60
        self.rendered_video = self.rendered_video.set_fps(60)
        # Set the audio of the video using the WAV file
        self.rendered_video = self.rendered_video.set_audio(
            AudioFileClip(self.wav_path)
        )
        print("Adding subtitles...")

        # Debug print to check subtitles content
        with open(self.srt_path, 'r') as file:
            srt_content = file.read()
            print("SRT Content:", srt_content)  # Debug print statement

        try:
            self.subtitles = SubtitlesClip(self.srt_path, self.__text_generator)
            self.subtitles = self.subtitles.set_position(('center', self.y_position), relative=True)

            # Trim the subtitles to match the video duration
            self.subtitles = self.subtitles.set_duration(self.rendered_video.duration)
        except Exception as e:
            print(f"Error initializing SubtitlesClip: {e}")
            return

        # Combine the video and the subtitles
        self.result = CompositeVideoClip(
            [self.rendered_video, self.subtitles]
        )

        # Set the duration of the final clip to match the rendered video
        self.result = self.result.set_duration(self.rendered_video.duration)

        # Save the video to the outputs folder
        self.result.write_videofile(
            output_path, fps=60, codec="libx264", bitrate="8000k"
        )
        print("Video rendered successfully!")
