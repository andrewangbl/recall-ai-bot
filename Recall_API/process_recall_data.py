import json
import re

def parse_recall_summary(summary, video_url):
    structured_summary = {
        "title": summary.get("name", ""),
        "cover": "",
        "tags": [],
        "summary": {},
        "video_url": video_url
    }

    # Extract cover image
    images = summary.get("images", [])
    if images:
        structured_summary["cover"] = images[0].get("urlOriginal", "")

    # Extract tags
    links = summary.get("links", [])
    structured_summary["tags"] = [link.get("item", {}).get("name", "") for link in links if link.get("item", {}).get("name")]

    # Parse markdown content
    markdown_content = summary.get("markdown", "")
    lines = markdown_content.split("\n")
    current_section = None

    for line in lines:
        if line.startswith("## "):
            # New section
            section_title = line[3:].split(" [(")[0].strip()
            current_section = section_title
            structured_summary["summary"][current_section] = []
        elif line.startswith("- "):
            # Bullet point
            bullet_point = line[2:]
            match = re.search(r'(.*) \[(.*?)\]\((.*?)\)', bullet_point)
            if match:
                text = match.group(1).strip()
                structured_summary["summary"][current_section].append(text)

    return structured_summary

# Read the raw data from file
input_file = "raw_recall_data.json"
with open(input_file, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Process the data
video_url = "https://www.youtube.com/watch?v=LEx2_zLobrM"  # You might want to store this in the raw data file as well
structured_summary = parse_recall_summary(raw_data, video_url)

# Output the structured summary to a file
output_file = "structured_summary.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(structured_summary, f, ensure_ascii=False, indent=2)

print(f"Structured summary saved to {output_file}")
