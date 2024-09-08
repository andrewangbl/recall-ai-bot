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
     d. Upload the videos to an AWS S3 bucket
     e. Post the videos as Instagram Reels

4. **Output**:
   - Generated videos will be saved in the `outputs` folder as `reel_output_p{part_number}.mp4`
   - Summaries and other data will be saved in the `operation_data` folder

5. **Customization**:
   - You can adjust video generation settings in the `autoeditor/generator.py` file:
     ```python
     # autoeditor/generator.py
     # startLine: 8
     # endLine: 95
     ```

6. **Monitoring**:
   - To change the time frame for checking new videos, modify the `hours_ago` parameter in the `get_latest_videos_rss` function:
     ```python
     # monitor/search.py
     # startLine: 7
     # endLine: 30
     ```

7. **Instagram Upload**:
   - The bot automatically uploads generated videos to Instagram using the `reel_upload.py` script.

**Note**: Ensure you have the necessary permissions and comply with YouTube's and Instagram's terms of service when using this bot.

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

4. **Upload and Posting**:
   - Generated videos are uploaded to an AWS S3 bucket.
   - The S3 URLs are then used to post the videos as Instagram Reels.

This automated process allows for efficient creation and distribution of content, transforming YouTube videos into engaging Instagram Reels with minimal manual intervention.

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

## FRQ or Notes for improvement in the future

### autoeditoer output
1. to manage autogenerate video audio srt output files path go to autoeditor/generator.py line 69 74.
2. to improve, make the audio piece not generated at outputs folder
3. strange temp out reel_output_p1TEMP_MPY_wvf_snd generated in root folder and is auto deleted

### script generated
control the json file input in workflow.py

### Adjust AI voice reading specified
autoeditor/generator.py line 50

### Adjust the length of separate video parts
pipeline.py line 25 char_limit and upper_limit

### Minimum Character Count for Video Generation

To ensure that only substantial content is processed into videos, a minimum character count check has been implemented. Videos with summaries shorter than the specified character count will be skipped. You can adjust this setting in the `pipeline.py` file:
```python
# Set the minimum character count for video generation
min_char_count = 800  # You can adjust this value as needed
```

This feature helps to filter out videos that might not have enough content for a meaningful summary or Reel.

### Caption and video script generation Prompt Engineering
change the prompt in recall_api/gpt_summary.py

### To change the Youtube channel to monitor
edit monitor/monitor_list.txt only.

### S3 Bucket Configuration
To configure the S3 bucket for video uploads, modify the `bucket_name` parameter in the `process_and_generate_video` function call in `pipeline.py`.

### Instagram Reel Upload
The Instagram Reel upload process is handled by the `reel_upload.py` script. To adjust the upload settings or modify the caption format, edit this file.

### Video Part Naming in S3
Videos are now stored in S3 with unique identifiers based on the YouTube video ID. This prevents overwriting when uploading multiple series of video summaries. The naming convention is `videos/{youtube_video_id}_p{part_number}.mp4`.


## Guide to get Instagram Access Token
1. Convert Personal Instagram Account to Professional Account

2. Get Facebook Business Page Id & save it

3. Link Facebook Page to Instagram Account

4. Generate Facebook Access Token using Instagram API

Permissions: all ig permissions, pages_manage_posts, pages_read_engagement

Select: get token


copy access token (it only last for 1 hours)

5. Get Instagram Account Id

{facebook_id}?fields=instagram_business_account&access_token={access_token}

## DynamoDB Tables

This project uses two DynamoDB tables:

1. **YouTubeChannelMonitor**: Stores information about the YouTube channels being monitored.
   - Partition key: `channel_name` (String)
   - Sort key: `channel_id` (String)

2. **VideoProcessingHistory**: Keeps track of processed videos to avoid duplicate processing.
   - Partition key: `video_url` (String)
   - Sort key: `processed_at` (String)

### Setting up DynamoDB Tables

To set up these tables in your AWS account, follow these steps:

1. Log in to the AWS Management Console.
2. Navigate to the DynamoDB service.
3. Click on "Create table" for each of the following tables:

#### YouTubeChannelMonitor Table
- Table name: YouTubeChannelMonitor
- Partition key: channel_name (String)
- Sort key: channel_id (String)

#### VideoProcessingHistory Table
- Table name: VideoProcessingHistory
- Partition key: video_url (String)
- Sort key: processed_at (String)

4. Leave other settings as default and click "Create".

### Managing YouTube Channels

To add, remove, or list YouTube channels in the YouTubeChannelMonitor table, use the functions in `monitor/manage_channels.py`:

- To add a channel:
  ```python
  add_channel("YouTubeChannelMonitor", "Channel Name", "UC1234567890")
  ```

- To remove a channel:
  ```python
  remove_channel("YouTubeChannelMonitor", "Channel Name")
  ```

- To list all channels:
  ```python
  list_channels("YouTubeChannelMonitor")
  ```

### Video Processing History

The VideoProcessingHistory table is automatically managed by the `pipeline.py` script. It adds entries when videos are processed and checks this table to avoid reprocessing videos.

Ensure your AWS credentials are properly configured to allow the script to interact with these DynamoDB tables.

### AWS Configuration

Before running the bot, make sure to configure your AWS credentials. Follow these steps:

1. Install the AWS CLI if you haven't already:
   ```
   sudo apt install awscli
   ```

2. Run the following command and enter your AWS credentials when prompted:
   ```
   aws configure
   ```

   You'll need to provide:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region name (e.g., us-west-2)
   - Default output format (you can press Enter to use the default)

3. Ensure that the AWS user associated with these credentials has the necessary permissions to access DynamoDB and S3.

This configuration allows the bot to interact with AWS services, including DynamoDB for storing channel and video processing information, and S3 for uploading generated videos.

### Folder Setup

Before running the bot, make sure to set up the following folders:

1. Create an `inputs` folder in the root directory:
   - This folder should contain MP4 files to be used as background videos for the generated reels.
   - You can download free stock videos from websites like [Pexels](https://www.pexels.com/videos/).

2. Create an `outputs` folder in the root directory:
   - This folder will store the generated video reels.

Ensure these folders exist and that the `inputs` folder contains at least one MP4 file before running the bot.

### Random Delay Between Video Uploads

To mimic human behavior and reduce the risk of being identified as a bot, the script implements a random delay between video uploads. This delay is set between 10 seconds to 10 minutes. You can adjust this range in the `pipeline.py` file:

```
delay = random.uniform(10, 600)  # Random delay between 10s to 10 minutes
```

This feature helps to make the upload pattern less predictable and more human-like.

# Deployment
Run prior setup and try running the script in the server.
Schedule script to run on AWS EC2 server every 24 hours using cron.
```crontab -e```
add this line:
```0 0 * * * /usr/bin/python3 /home/ubuntu/recall-ai-bot/pipeline.py >> /home/ubuntu/recall-ai-bot/pipeline.log 2>&1```
It should run ever 24 hours at midnight on the server local time. 

Note: AWS might have risk of ig page being suspended as per our experimentation.
