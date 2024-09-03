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
    prompt = f"""
     Your task is to enhance the following structured summary of a video into a more engaging and cohesive narrative. The output should be a JSON structure with the following fields:

    - title: An attention-grabbing title (string)
    - cover: The cover image URL (string)
    - caption: A brief, engaging caption for social media (string)
    - tags: Relevant hashtags (array of strings)
    - script: An array of objects, each containing:
      - text: A sentence or short paragraph (string)
      - timestamp: The original timestamp, if available (string)
      - url: The original URL, if available (string)

    For the script:
    1. At the beginning of the script, mention the original Youtube video is generated by Recall AI.
    2. Maintain the key points from the original summary.
    3. Add transitions and context between points for a smoother narrative flow.
    4. For added transitions or context, leave timestamp and url blank.
    5. Aim for a mix of short, impactful sentences and slightly longer explanatory ones.
    6. Ensure the narrative builds tension and interest throughout.

    Here's the structured summary to enhance:

    {json.dumps(structured_summary, indent=2)}

    Please provide the enhanced summary in a valid JSON format. In caption, mentioned Recall AI and its official website https://www.getrecall.ai/ and in caption please attach at least 5 hashtags related to the video, including #RecallAI.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert storyteller and content creator for promoting a company called Recall AI. Recall AI's software product is for generating summaries of Youtube videos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print("Error decoding JSON response from OpenAI API")
            print("Raw content:", content)
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

    if enhanced_summary is None:
        print("Retrying with a simplified prompt...")
        simplified_summary = {
            "title": structured_summary["title"],
            "cover": structured_summary["cover"],
            "tags": structured_summary["tags"],
            "summary": {k: v[:3] for k, v in structured_summary["summary"].items()}  # Limit to first 3 items per section
        }
        enhanced_summary = generate_enhanced_summary(simplified_summary)

    if enhanced_summary:
        save_enhanced_summary(enhanced_summary, output_file)
        print(f"Enhanced summary saved to {output_file}")
    else:
        print("Failed to generate enhanced summary")

if __name__ == "__main__":
    main()
