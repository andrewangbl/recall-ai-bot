# recall-ai-bot

## Usage

To use the recall-ai-bot, follow these steps:

1. **Setup**:
   - Install the required dependencies:
     ```
     pip install -r requirements.txt
     ```
   - Set up your environment variables in a `.env` file. Include the following:
     - `RECALL_API_SECRET`: Your Recall API key
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `INSTAGRAM_ACCESS_TOKEN`: Your Instagram access token
     - `INSTAGRAM_ACCOUNT_ID`: Your Instagram account ID

2. **Configure YouTube Channels**:
   - Edit the `monitor/monitor_list.txt` file to include the YouTube channels you want to monitor. Each line should contain the channel name and ID, separated by a comma:
     ```
     Channel: Bloomberg Technology, UCrM7B7SL_g1edFOnmj-SDKg
     Channel: Andrew Huberman, UC2D2CMWXMOVWx7giW1n3LIg
     ```

3. **Run the Bot**:
   - Execute the main script:
     ```
     python pipeline.py
     ```
   - The bot will perform the following actions:
     a. Check for new videos from the specified channels
     b. Process new videos to generate summaries
     c. Create Instagram Reel videos from the summaries
     d. (Future feature) Upload the videos to Instagram

4. **Output**:
   - Generated videos will be saved in the `outputs` folder as `reel_output_p{part_number}.mp4`
   - Summaries and other data will be saved in the `operation_data` folder

5. **Customization**:
   - You can adjust video generation settings in the `autoeditor/generator.py` file:
   ```
   python:autoeditor/generator.py
  startLine: 8
  endLine: 95
   ```


6. **Monitoring**:
   - To change the time frame for checking new videos, modify the `hours_ago` parameter in the `get_latest_videos_rss` function:
```
python:monitor/search.py
startLine: 7
endLine: 30
```


7. **Instagram Upload** (Future Feature):
   - Once implemented, the bot will automatically upload generated videos to Instagram using the `reel_upload.py` script.

Note: Ensure you have the necessary permissions and comply with YouTube's and Instagram's terms of service when using this bot.



## How It Works

The recall-ai-bot operates through the following process:

1. **YouTube Channel Monitoring**:
   - The bot starts by executing the `pipeline.py` code.
   - It uses the `monitor` module to check if any YouTube channels listed in `monitor_list.txt` have uploaded new videos within the last 24 hours.
   - The module returns a list of YouTube URLs for new videos.

2. **Video Processing**:
   - The bot iterates through the list of URLs.
   - For each URL, it uses the `recall_api` module to generate:
     a. A summary script
     b. An Instagram Reel caption
   - Both are returned in JSON format.

3. **Video Generation**:
   - The `autoeditor` module is used to convert the script into one or more Instagram Reel videos.
   - If a script is too long for a single Reel, it's automatically split into multiple parts.

4. **Upload and Posting** (Upcoming Feature):
   - Generated videos will be uploaded to an AWS S3 bucket.
   - The S3 URLs will then be used to post the videos as Instagram Reels.

This automated process allows for efficient creation and distribution of content, transforming YouTube videos into engaging Instagram Reels with minimal manual intervention.

## Next Development we need to finish this for MVP

The final step of uploading to AWS S3 and posting to Instagram is currently under development. Once implemented, this feature will complete the automation pipeline, allowing for seamless content distribution from YouTube to Instagram Reels.

## Key Components

1. pipeline.py: The main orchestrator of the entire process.
This script coordinates the entire workflow, from monitoring YouTube channels to generating and processing videos.

2. monitor/search.py: Handles YouTube channel monitoring and video retrieval.
This module checks for new videos from specified YouTube channels and retrieves the most viewed recent videos.

3. recall_api/workflow.py: Processes video URLs to generate structured summaries.
This component interacts with the Recall API to fetch and process video data, generating enhanced summaries.

4. autoeditor/generator.py: Converts scripts into video content.
This module handles the generation of video content from the processed scripts, including audio synthesis and video editing.

5. autoeditor/editor.py: Manages video editing and composition.
This class is responsible for combining various elements (background video, subtitles, cover images) into the final video output.

## Notes for improvement in the future (skip this now for current MVP)

### autoeditoer output
1. to manage autogenerate video audio srt output files path go to autoeditor/generator.py line 69 74.
2. to improve, make the audio piece not generated at outputs folder
3. strange temp out reel_output_p1TEMP_MPY_wvf_snd generated in root folder and is auto deleted

### script generated
control the json file input in workflow.py
