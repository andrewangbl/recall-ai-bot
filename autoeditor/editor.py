from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips, vfx, ImageClip
import random
import math
import os


class VideoEditor:
    def __init__(self, clip_duration, srt_path, wav_path, animate_text=True, clip_generation_mode="normal", part_number=1):
        """
        Initialize the Editor object.

        Args:
            reddit_id (str): The ID of the Reddit post.
            clip_duration (int): The duration of the video clip in seconds.
            srt_path (str): The path to the SRT file.
            wav_path (str): The path to the WAV file.
            animate_text (bool): Whether to animate the text or not.
            clip_generation_mode (str): The mode for generating video clips.
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
        # The mode for generating video clips.
        self.clip_generation_mode = clip_generation_mode
        # A list of background videos
        self.bg_videos = [f for f in os.listdir("inputs") if f.endswith('.mp4')]
        # Randomly select a background video to use later
        self.bg_path = random.choice(self.bg_videos)
        self.background_video = VideoFileClip(
            os.path.join("inputs", self.bg_path))
        self.background_video = self.crop_and_resize_video()

        # Default vertical position (70% from top)
        self.y_position = 0.5
        self.cover_img_url = None
        self.part_number = part_number

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
            fontsize = 54
        elif len(txt) > 50:
            fontsize = 60
        else:
            fontsize = 66

        return TextClip(
            txt,
            font='Arial-Bold', fontsize=fontsize,
            stroke_color='black', stroke_width=2.5,
            color='white', method='caption', size=(850, None),
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

    def create_part_subtitle(self):
        part_text = f"Part {self.part_number}"
        part_clip = TextClip(part_text, fontsize=100, color='white', font='Arial-Bold', stroke_color='black', stroke_width=3)
        part_clip = part_clip.set_position(('center', 0.1), relative=True).set_duration(5)  # Increased duration to 5 seconds
        return part_clip

    def start_render(self, output_path="outputs/output.mp4"):
        """
        Starts the rendering process by creating a video clip with subtitles.

        Args:
            output_path (str): The path to save the rendered video file. Default is "outputs/output.mp4".

        Returns:
            None
        """
        print("Rendering video...")

        if self.clip_generation_mode == "normal":
            self.upperlimit_time = (
                self.background_video.duration -
                math.ceil(10 * self.clip_duration) / 10
            )
            self.start_time = random.randint(0, math.floor(self.upperlimit_time))
            print(
                f"Start time: {self.start_time} seconds |",
                f"End time: {self.start_time + self.clip_duration} seconds"
            )
            self.rendered_video = self.background_video.subclip(
                self.start_time,
                self.start_time + self.clip_duration
            )
        elif self.clip_generation_mode == "combine":
            self.rendered_video = self.combine_video_clips()
        else:
            raise ValueError("Invalid clip generation mode")

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
            self.subtitles = self.subtitles.set_position(('center', 0.8), relative=True)

            # Trim the subtitles to match the video duration
            self.subtitles = self.subtitles.set_duration(self.rendered_video.duration)
        except Exception as e:
            print(f"Error initializing SubtitlesClip: {e}")
            return

        # Process cover image
        if self.cover_img_url:
            try:
                cover_img = ImageClip(self.cover_img_url)
                cover_img = cover_img.resize(height=500)  # Increase height to 600
                cover_img = cover_img.set_position(('center', 0.2), relative=True)  # Move higher to 20% from top
                cover_img = cover_img.set_duration(self.rendered_video.duration)
            except Exception as e:
                print(f"Error processing cover image: {e}")
                cover_img = None
        else:
            cover_img = None

        # Move subtitles higher
        self.subtitles = self.subtitles.set_position(('center', 0.5), relative=True)  # Move to 50% from top (middle)

        # Create part subtitle
        part_subtitle = self.create_part_subtitle()

        # Combine the video, subtitles, cover image, and part subtitle
        clips_to_combine = [self.rendered_video, self.subtitles, part_subtitle]
        if cover_img:
            clips_to_combine.append(cover_img)

        self.result = CompositeVideoClip(clips_to_combine)

        # Set the duration of the final clip to match the rendered video
        self.result = self.result.set_duration(self.rendered_video.duration)

        # Save the video to the outputs folder
        self.result.write_videofile(
            output_path, fps=30, codec="libx264", bitrate="4000k",
            preset='faster', threads=4
        )
        print("Video rendered successfully!")

    def crop_and_resize_video(self, video_clip=None, target_aspect_ratio=9/16, target_width=1080):
        if video_clip is None:
            video_clip = self.background_video

        # Get the current video dimensions
        current_width, current_height = video_clip.w, video_clip.h
        current_aspect_ratio = current_width / current_height

        if current_aspect_ratio > target_aspect_ratio:
            # Video is too wide, crop the sides
            new_width = int(current_height * target_aspect_ratio)
            crop_amount = (current_width - new_width) // 2
            cropped = video_clip.crop(x1=crop_amount, x2=current_width-crop_amount)
        else:
            # Video is too tall, crop the top and bottom
            new_height = int(current_width / target_aspect_ratio)
            crop_amount = (current_height - new_height) // 2
            cropped = video_clip.crop(y1=crop_amount, y2=current_height-crop_amount)

        # Resize the cropped video to the target width
        target_height = int(target_width / target_aspect_ratio)
        resized = cropped.resize(width=target_width, height=target_height)

        return resized

    def combine_video_clips(self):
        combined_clip = None
        total_duration = 0
        fade_duration = 0.5  # Duration of the fade effect in seconds

        while total_duration < self.clip_duration:
            if not self.bg_videos:
                raise ValueError("Not enough background videos to cover the audio duration")

            next_clip_path = random.choice(self.bg_videos)
            self.bg_videos.remove(next_clip_path)
            next_clip = VideoFileClip(os.path.join("inputs", next_clip_path))
            next_clip = self.crop_and_resize_video(next_clip)

            if combined_clip is None:
                combined_clip = next_clip
            else:
                # Add fade out to the end of the current clip
                combined_clip = combined_clip.fx(vfx.fadeout, duration=fade_duration)

                # Add fade in to the start of the next clip
                next_clip = next_clip.fx(vfx.fadein, duration=fade_duration)

                # Concatenate the clips
                combined_clip = concatenate_videoclips([combined_clip, next_clip], method="compose")

            total_duration = combined_clip.duration

        if total_duration > self.clip_duration:
            combined_clip = combined_clip.subclip(0, self.clip_duration)

        return combined_clip
