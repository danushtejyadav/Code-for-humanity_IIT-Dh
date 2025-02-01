import os
from moviepy.audio.io.AudioFileClip import AudioFileClip
import requests
from bs4 import BeautifulSoup
import json
from groq import Groq
from dotenv import load_dotenv
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import pyttsx3
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS,cross_origin
import shutil


app = Flask(__name__)
CORS(app)
# Load environment variables
load_dotenv()

grok_key = os.getenv("GROQ_API_KEY3")
groq_client = Groq(api_key=grok_key)

app = Flask(__name__)

def get_news(query, api_key):
    url = "https://newsapi.org/v2/everything"
    params = {'qInTitle': query, 'sortBy': 'relevancy', 'language': 'en', 'pageSize': 10, 'apiKey': api_key}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []
    data = response.json()
    seen_urls = set()
    unique_articles = []
    for article in data.get("articles", []):
        url = article["url"]
        if url not in seen_urls and len(unique_articles) < 3:
            seen_urls.add(url)
            unique_articles.append(article)
    return unique_articles

def scrape_text_and_images(url, folder_name):
    os.makedirs(folder_name, exist_ok=True)
    clear_folder(folder_name)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    text_content = soup.get_text(separator='\n', strip=True)
    text_file = os.path.join(folder_name, "article.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text_content)
    img_tags = soup.find_all('img', src=True)
    for i, img in enumerate(img_tags[:5], 1):
        img_url = urljoin(url, img['src'])
        img_response = requests.get(img_url)
        img_filename = os.path.join(folder_name, f"image_{i}.jpg")
        with open(img_filename, 'wb') as f:
            f.write(img_response.content)


    return text_content

def llama_assistant(prompt):
    sys_msg = "You are a helpful AI assistant summarizing articles. Provide a concise summary in bullet points (max 50 words)."
    response = groq_client.chat.completions.create(
        messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': prompt}],
        model='llama-3.2-90b-vision-preview'
    )
    return response.choices[0].message.content.strip()

def generate_audio(summary, folder_name):
    tts = pyttsx3.init()
    audio_file = os.path.join(folder_name, "summary_audio.mp3")
    tts.save_to_file(summary, audio_file)
    tts.runAndWait()
    return audio_file
def clear_folder(folder_name):
    """Remove all existing files in the folder to ensure fresh images."""
    if os.path.exists(folder_name):
        for file in os.listdir(folder_name):
            file_path = os.path.join(folder_name, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    else:
        os.makedirs(folder_name, exist_ok=True)
def resize_images(image_files, target_size=(1280, 720)):
    resized_images = []
    for img_path in image_files:
        img = Image.open(img_path)
        img = img.convert("RGB")    
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        resized_path = img_path.replace(".", "_resized.")
        img.save(resized_path, "JPEG")
        resized_images.append(resized_path)
    return resized_images

def create_video (folder_name, audio_file):
    image_files = sorted([os.path.join(folder_name, f) for f in os.listdir(folder_name) if f.startswith("image_") and f.endswith(".jpg")])
    if not image_files:
        return None
    resized_images = resize_images(image_files)
    if not resized_images:
        return None  # No valid images found

    # Load audio file
    audio = AudioFileClip(audio_file)
    audio_duration = audio.duration

    # Calculate the number of times images should loop
    image_duration = 3  # Each image will be displayed for 3 seconds
    total_images_needed = int(audio_duration // image_duration) + 1
    looped_images = (resized_images * ((total_images_needed // len(resized_images)) + 1))[:total_images_needed]

    # Create video from images
    clip = ImageSequenceClip(looped_images, durations=[image_duration] * len(looped_images))

    # Trim video duration to exactly match the audio duration
    final_duration = min(clip.duration, audio_duration)
    clip = clip.set_duration(final_duration)

    # Trim audio to exactly match the final video duration
    audio = audio.subclip(0, final_duration)
    clip = clip.set_audio(audio)

    # Save the final video
    video_file = os.path.join(folder_name, "summary_video.mp4")
    clip.write_videofile(video_file, codec="libx264", fps=24)
    copy_video_to_static_folder(folder_name)
    return video_file


def copy_video_to_static_folder(folder_name):
    # Path of the final video file
    video_file = os.path.join(folder_name, "summary_video.mp4")
    
    # Ensure the video exists in the folder
    if os.path.exists(video_file):
        # Path where you want to copy the video file
        static_video_folder = os.path.join('static', 'videos')
        os.makedirs(static_video_folder, exist_ok=True)  # Make sure the folder exists
        
        # Get the current number of video files in the folder
        existing_videos = os.listdir(static_video_folder)
        video_count = len([f for f in existing_videos if f.endswith('.mp4')])
        
        # Create a new file name with an index number
        new_video_name = f"summary_video_{video_count + 1}.mp4"
        new_video_path = os.path.join(static_video_folder, new_video_name)
        
        # Copy the video to the static folder with the new name
        shutil.copy(video_file, new_video_path)
        
        # Optionally clear the folder if needed
        clear_folder(folder_name)
        
        # Return the relative URL to the copied video
        return f"/static/videos/{new_video_name}"
    return None

# @app.route('/')
# def home():
#     return render_template('index.html')

import os

@app.route('/news_generate', methods=['POST'])
@cross_origin()
def generate():
    data = request.get_json()
    query = data.get("query")
    api_key = os.getenv("NEWSAPI")
    
    if not api_key:
        return jsonify({"error": "Missing API key"}), 400
    
    articles = get_news(query, api_key)
    if not articles:
        return jsonify({"error": "No articles found"}), 404
    
    results = []
    for i, article in enumerate(articles, 1):
        url = article["url"]
        folder_name = f"news_output_{i}"
        scraped_text = scrape_text_and_images(url, folder_name)
        summary = llama_assistant(scraped_text)
        audio_file = generate_audio(summary, folder_name)
        video_file = create_video(folder_name, audio_file)
        
        # Copy video to the static folder
        copy_video_to_static_folder(folder_name)

        results.append({
            "article": url, 
            "summary": summary,  # This is a string with the summary
            "audio": audio_file, 
            "video": video_file
        })

    # Get list of video files in static/videos folder
    video_files = [f"/backend/static/videos/{file}" for file in os.listdir('static/videos') if file.endswith('.mp4')]

    return jsonify({"results": results, "videos": video_files})


if __name__ == "__main__":
    app.run(debug=True)
