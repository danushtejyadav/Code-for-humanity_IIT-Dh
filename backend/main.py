import os
import requests
import threading
from dotenv import load_dotenv
import time
from groq import Groq
import shelve
import re
from pydub import AudioSegment
import base64
from flask import Flask,render_template, request, jsonify,send_file
from moviepy.editor import *
from natsort import natsorted
from deepgram import DeepgramClient, SpeakOptions

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Hugging Face API Keys
hugging_face_api_keys = [
    os.getenv("HUGGING_FACE_API_KEY_1"),
    os.getenv("HUGGING_FACE_API_KEY_2")
]
api_key_index = 0  # To track alternating API keys
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY3"))
bhashini_key = os.getenv('BHASHINI_API_KEY')

AudioSegment.converter = r"ffmpeg.exe"
TTS_FOLDER = 'tts_uploads'
os.makedirs(TTS_FOLDER, exist_ok=True)

# Create necessary folders and clear memory folder on startup
os.makedirs("s1", exist_ok=True)
if os.path.exists("memory"):
    for file in os.listdir("memory"):
        os.remove(os.path.join("memory", file))
else:
    os.makedirs("memory")

def get_next_api_key():
    global api_key_index
    api_key = hugging_face_api_keys[api_key_index]
    api_key_index = (api_key_index + 1) % len(hugging_face_api_keys)
    return api_key

# Image Generation Function
def image_gen(prompt, scene_index):
    headers = {"Authorization": f"{get_next_api_key()}"}
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        response.raise_for_status()
        if response.status_code == 200:
            filename = f"s1/generated_image_{scene_index}.png"
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
    except Exception as e:
        print(f"Error generating image for Scene {scene_index}: {e}")
    return None

# Full Story Generation
def full_story(prompt):
    sys_msg = (
        'You will generate full short story with scenes to conceptualise the users request. '
        'The story should be relavent to the prompt and provide explanation. '
        "The story should have a meaning and be informative."
        'Generate a short story with maximum of 5 scenes.'
        'It should be easy to visualise the story and should have a clear beginning, middle, and end. '
        )
    convo = [{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# Scene Generation
def scene_generator(full_story_text, memory):
    sys_msg = (
        "Given a story you will generate a detailed scene. Your scene should be engaging, character-driven, and relevant to the story context. "
        "Ensure consistency with the overall story setting and characters. "
        "You can generate up to 5 scenes for the story. "
        "Describe the scene in a few sentences. "
        'You will generate one scene at a given time. '
        'You will start with scene name and scene description do not include any other details or cross questions.'
        "If all scenes have been generated, respond with 'Scene generation complete'."
        
    )

    convo = memory + [{"role": "system", "content": sys_msg}, {"role": "user", "content": full_story_text}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

def scene_summariser(full_story_text, memory):
    sys_msg = (
        "Given given a detailed description of scene. Your scene should be engaging, character-driven, and relevant to the story context. "
        "Ensure consistency with the overall story setting and characters.  "
        "Describe the scene in a few sentences. "
        "You will summarise the scene and provide a brief description of the scene. "
        "You will not ask any questions or provide any other details. "
    )

    convo = memory + [{"role": "system", "content": sys_msg}, {"role": "user", "content": full_story_text}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# Dialogue Generation
def dialogue_gen(scene):
    sys_msg = (
  "You are dialogue writer for the given scene description You will create very short dialogues relavent to the scene . "
  "Your dialogues should be like a narrator , as if you are narrating the scene. "
  "You will not miss out on key details and emotions of the characters. "
  "Do not ask questions or provide any other details."
  "Directly start with the narrator dialogue do not say Here is your dialogue."
     )
    convo = [{"role": "system", "content": sys_msg}, {"role": "user", "content": scene}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# Image Prompt Generation
def image_prompt_gen(full_story_text, previous_prompts, scene):
    sys_msg = (
        "You are a professional concept artist and scene designer. "
        "Given a scene description, the full story, and previous prompts, generate a highly detailed and realistic image prompt "
        "for an AI image generation model. "
        "Your prompt should emphasize key visual elements such as lighting, color tones, character expressions, background details, and dynamic actions. "
        "Ensure consistency with previous images and the overall story setting."

    )
    convo = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": f"Full Story: {full_story_text}"},
        {"role": "user", "content": f"Previous Prompts: {previous_prompts}"},
        {"role": "user", "content": f"Scene: {scene}"}
    ]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# ASR + TTS Function
def bhashini_tts(query, target_lang,scene_index):
    service_id = "ai4bharat/indictrans-v2-all-gpu--t4"

    # Determine TTS service ID based on target language
    if target_lang in ["hi", "as", "gu", "mr", "or", "pa", "bn"]:
        service_id_tts = "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4"
    elif target_lang in ["kn", "ml", "ta", "te"]:
        service_id_tts = "ai4bharat/indic-tts-coqui-dravidian-gpu--t4"
    elif target_lang in ["en", "brx", "mni"]:
        try:
            SPEAK_OPTIONS = {"text": query} 
        # STEP 1: Create a Deepgram client.
        # By default, the DEEPGRAM_API_KEY environment variable will be used for the API Key
            deepgram = DeepgramClient()

        # STEP 2: Configure the options (such as model choice, audio configuration, etc.)
            options = SpeakOptions(
                model="aura-asteria-en",
        )

        # STEP 3: Call the save method on the speak property
            filename = f"tts_{scene_index}.mp3"
            file_path = os.path.join(TTS_FOLDER, filename)
            response = deepgram.speak.rest.v("1").save(file_path, SPEAK_OPTIONS, options)
            
            return response



        except Exception as e:
            print(f"Exception: {e}")

    # Request headers (unchanged)
    headers = {
        "Postman-Token": "<calculated when request is sent>",
        "Content-Type": "application/json",
        "Content-Length": "<calculated when request is sent>",
        "Host": "<calculated when request is sent>",
        "User-Agent": "PostmanRuntime/7.40.0",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "User-Agent": "Python",
        "Authorization": bhashini_key
    }

    # Request body
    body = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": "en",
                        "targetLanguage": target_lang
                    },
                    "serviceId": service_id
                }
            },
            {
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": target_lang
                    },
                    "serviceId": service_id_tts,
                    "gender": "female",
                    "samplingRate": 8000
                }
            }
        ],
        "inputData": {
            "input": [
                {
                    "source": query
                }
            ]
        }
    }
        # Parse the JSON response
    response1 = requests.post("https://dhruva-api.bhashini.gov.in/services/inference/pipeline", headers=headers,json=body)
    response_data = response1.json()
    audio_data = base64.b64decode(response_data['pipelineResponse'][1]['audio'][0]['audioContent'])
    filename = f"tts_{scene_index}.wav"
    file_path = os.path.join(TTS_FOLDER, filename)
    with open(file_path, "wb") as audio_file:
        audio_file.write(audio_data)
    return file_path


# Merge Images and Audio into Video


def create_dynamic_video():
    # Load and pair files
    image_dir = 's1'
    audio_dir = 'tts_uploads'  # Removed the trailing comma
    output_path = 'output_movie.mp4'  # Removed the trailing comma
    fps = 24
    zoom_factor = 0.3

    images = natsorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
    audios = natsorted([f for f in os.listdir(audio_dir) if f.endswith('.wav')or f.endswith('.mp3')])

    while len(images) != len(audios):
        print("Length not equal. Waiting for files to be ready...")
        images = natsorted([f for f in os.listdir(image_dir) if f.endswith('.png')or f.endswith('.mp3')])
        time.sleep(10)

    print("Creating dynamic video...")
    
    clips = []

    for img_file, audio_file in zip(images, audios):
        # Create audio clip
        audio_path = os.path.join(audio_dir, audio_file)
        audio = AudioFileClip(audio_path)

        # Create image clip with dynamic zoom effect
        img_path = os.path.join(image_dir, img_file)
        img_clip = (ImageClip(img_path)
                    .set_duration(audio.duration)
                    .set_audio(audio)
                    .resize(lambda t: 1 + zoom_factor * (t / audio.duration))  # Dynamic zoom effect
                    .set_position('center'))

        clips.append(img_clip)

    # Combine clips into a single video
    final_clip = concatenate_videoclips(clips, method="compose")

    # Write the final video file
    final_clip.write_videofile(output_path, fps=fps, codec='libx264')

# Main Story Generation Function
def generate_story(user_prompt,lang_code):
    # Initialize memory using shelve
    with shelve.open("memory/story_memory") as db:
        if "full_story" not in db:
            db["full_story"] = full_story(user_prompt)
            db["scenes"] = []
            db["scene_index"] = 1
            db["generating"] = True
        full_story_text = db["full_story"]
        scenes = db["scenes"]
        scene_index = db["scene_index"]
        generating = db["generating"]

    # Lists to store generated image and audio paths
    image_paths = []
    audio_paths = []
    image_lock = threading.Lock()  # Lock for thread-safe updates to image_paths
    audio_lock = threading.Lock()  # Lock for thread-safe updates to audio_paths

    # Scene Generation Loop
    while generating:
        with shelve.open("memory/story_memory") as db:
            scene = scene_generator(full_story_text, db["scenes"])
            # Check for completion
            scene_sum = scene_summariser(scene, db["scenes"])
            print(scene_sum)
            pattern = r"(?i)\bscene\s+generation\s+complete\b"
            if re.search(pattern, scene.strip()):
                db["generating"] = False
                print("Scene generation complete. Stopping further scene generation.")
                break

            # Append the new scene to memory
            scenes.append({"role": "user", "content": scene})
            db["scenes"] = scenes

        # Generate dialogue and image description
        dialogue = dialogue_gen(scene)

        # Generate TTS audio in a separate thread
        def save_and_display_audio():
            audio_path = bhashini_tts(dialogue,lang_code,scene_index)
            if audio_path:
                with audio_lock:  # Ensure thread-safe updates to audio_paths
                    audio_paths.append(audio_path)
                print(f"Audio saved for Scene {scene_index}: {audio_path}")

        threading.Thread(target=save_and_display_audio).start()

        image_description = scene

        # Generate image prompt with memory of full story and previous prompts
        previous_prompts = [s["content"] for s in scenes[:-1]]  # Exclude current scene
        image_prompt = image_prompt_gen(full_story_text, previous_prompts, image_description)

        # Generate image in a separate thread
        def save_and_display_image():
            image_path = image_gen(image_prompt, scene_index)
            if image_path:
                with image_lock:  # Ensure thread-safe updates to image_paths
                    image_paths.append(image_path)
                print(f"Image saved for Scene {scene_index}: {image_path}")

        threading.Thread(target=save_and_display_image).start()

        scene_index += 1
        with shelve.open("memory/story_memory") as db:
            db["scene_index"] = scene_index

    print("## Story Generation Complete. Waiting for images and audio to finish rendering...")
    create_dynamic_video()





def main():
    user_prompt = input("Enter the topic for the story: ")
    lang = input("Enter the language code: ")
    if user_prompt:
        generate_story(user_prompt,lang)

if __name__ == "__main__":
    main()
