import json
import os
from openai import OpenAI
from dotenv import load_dotenv


# Because pytube package is not working, we will not use this prompt. But I kept it here for future reference and improvement



# Load environment variables
load_dotenv()

# Set up OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_structured_summary(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def generate_enhanced_summary(structured_summary):
    functions = [
        {
            "name": "create_enhanced_summary",
            "description": "Create an enhanced summary of a video for an Instagram Reel in a specific JSON format",
            "parameters": {
                "type": "object",
                "properties": {
                    "cover": {"type": "string", "description": "The cover image URL"},
                    "caption": {"type": "string", "description": "An engaging caption for Instagram Reel, including key points and hashtags"},
                    "script": {"type": "array", "items": {"type": "string"}, "description": "An array of strings, each containing a sentence or short paragraph for the Reel script"}
                },
                "required": ["cover", "caption", "script"]
            }
        }
    ]

    prompt = f"""
    Enhance the following structured summary of a video into an engaging Instagram Reel script and caption.
    For the script:
    1. Start by mentioning the original YouTube video's title: "{structured_summary.get('title', 'Untitled Video')}" Then, mention that this video is summarized by Recall.
    2. Add transitions and context for a smoother narrative flow when necessary.
    3. Aim for impactful short sentences suitable for Instagram Reel.
    4. Do not include any questions in the script. Questions are not suitable for AI voice narration as they cannot be read with proper intonation.
    5. Avoid using parentheses for explanations, as AI will read the text within them verbatim.
    6. Include a clear and engaging ending to the script, encouraging viewers to check out the full summary using Recall's AI tool.

    For the caption:
    1. Pose a question or make a statement that captures the main theme of the video. Introduce the key topics covered in the video in one sentence
    2. Mention Recall and its official website https://www.getrecall.ai/. Invite users to check out the original video and use Recall's AI tool for the FULL summaries.
    3. Include the original YouTube video URL: {structured_summary.get('video_url', '')}.
    4. Select at least 5 relevant hashtags from the "tags" field provided in the structured summary, and include #RecallAI as one of the hashtags.

    Here's the structured summary to enhance:

    {json.dumps(structured_summary, indent=2)}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert storyteller and Instagram Reels content creator for promoting a company called Recall. Recall's product is for quickly summarizing Youtube videos and podcasts."},
                {"role": "user", "content": prompt}
            ],
            functions=functions,
            function_call={"name": "create_enhanced_summary"},
            temperature=0.7,
            max_tokens=4000
        )

        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "create_enhanced_summary":
            return json.loads(function_call.arguments)
        else:
            print("Unexpected response format from OpenAI API")
            return None
    except Exception as e:
        print(f"An error occurred while calling the OpenAI API: {e}")
        return None

def save_enhanced_summary(enhanced_summary, output_file):
    with open(output_file, 'w') as file:
        json.dump(enhanced_summary, file, indent=2)

def main():
    input_file = "structured_summary.json"
    output_file = "enhanced_summary.json"

    structured_summary = load_structured_summary(input_file)
    enhanced_summary = generate_enhanced_summary(structured_summary)

    # Check if the initial attempt to generate an enhanced summary failed
    if enhanced_summary is None:
        print("Retrying with a simplified prompt...")

        # Create a simplified version of the summary
        simplified_summary = {
            "cover": structured_summary["cover"],
            "tags": structured_summary["tags"],
            # Limit each section of the summary to its first 3 items
            # This creates a shorter, more concise version of the summary
            "summary": {k: v[:3] for k, v in structured_summary["summary"].items()},
            "video_url": structured_summary.get("video_url", "")
        }

        # Attempt to generate an enhanced summary again using the simplified version
        enhanced_summary = generate_enhanced_summary(simplified_summary)

    # Check if the enhanced summary was successfully generated
    # (either on the first attempt or with the simplified version)
    if enhanced_summary:
        save_enhanced_summary(enhanced_summary, output_file)
        print(f"Enhanced summary for Instagram Reel saved to {output_file}")
    else:
        print("Failed to generate enhanced summary for Instagram Reel")

if __name__ == "__main__":
    main()
