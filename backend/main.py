import os
import requests
import threading
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq
import shelve
import re
from pydub import AudioSegment
import base64
from flask import Flask, request, jsonify , render_template
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Load environment variables
load_dotenv()

# Hugging Face API Keys
hugging_face_api_keys = [
    os.getenv("HUGGING_FACE_API_KEY_1"),
    os.getenv("HUGGING_FACE_API_KEY_2")
]
api_key_index = 0  # To track alternating API keys
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY2"))
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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"s1/generated_image_{scene_index}_{timestamp}.png"
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
    except Exception as e:
        print(f"Error generating image for Scene {scene_index}: {e}")
    return None

# Full Story Generation
def full_story(prompt):
    sys_msg = (
        'You are an expert creative writer specializing in immersive storytelling. '
        'Generate a well-structured, engaging, and coherent short story based on the given prompt. '
        'Ensure a clear narrative arc with an intriguing beginning, well-paced development, and a satisfying conclusion. '
        'Use vivid yet concise descriptions to create a strong sense of place and atmosphere. '
        )
    convo = [{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# Scene Generation
def scene_generator(full_story_text, memory):
    sys_msg = (
        "You are an expert at cinematic scene generation. Given a full short story, generate one scene at a time "
        "in a way that maintains narrative continuity. Each scene should be self-contained yet contribute to the overarching plot. "
        "Ensure vivid, highly visual descriptions focusing on setting, character actions, and emotions. "
        "Avoid redundancy while ensuring seamless transitions between scenes. "
        "If all scenes have been generated, respond with 'Scene generation complete'."
    )

    convo = memory + [{"role": "system", "content": sys_msg}, {"role": "user", "content": full_story_text}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# Dialogue Generation
def dialogue_gen(scene):
    sys_msg = (
        "You are a dialogue expert, skilled at crafting natural and emotionally engaging conversations. "
        "Given a scene, generate a compelling dialogue for one character that fits within the context. "
        "The dialogue should be authentic, expressive, and contribute to character development or plot progression. "
        "Ensure it remains concise yet impactful, matching the character’s personality and the overall mood of the story."
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
def bhashini_tts(query):
    target_lang = "kn"
    service_id = "ai4bharat/indictrans-v2-all-gpu--t4"

    # Determine TTS service ID based on target language
    if target_lang in ["hi", "as", "gu", "mr", "or", "pa", "bn"]:
        service_id_tts = "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4"
    elif target_lang in ["kn", "ml", "ta", "te"]:
        service_id_tts = "ai4bharat/indic-tts-coqui-dravidian-gpu--t4"
    elif target_lang in ["en", "brx", "mni"]:
        service_id_tts = "ai4bharat/indic-tts-coqui-misc-gpu--t4"

    # Request headers (unchanged)
    headers = {
        "Postman-Token": "<calculated when request is sent>",
        "Content-Type": "application/json",
        "Content-Length": "<calculated when request is sent>",
        "Host": "<calculated when request is sent>",
        "User-Agent": "PostmanRuntime/7.40.0",
        "Accept": "/",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Accept": "/",
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
    response1 = requests.post("https://dhruva-api.bhashini.gov.in/services/inference/pipeline", headers=headers, json=body)
    response_data = response1.json()
    audio_data = base64.b64decode(response_data['pipelineResponse'][1]['audio'][0]['audioContent'])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tts_{timestamp}.wav"
    file_path = os.path.join(TTS_FOLDER, filename)
    with open(file_path, "wb") as audio_file:
        audio_file.write(audio_data)
    return file_path

# Main Story Generation Function
def generate_story(user_prompt):
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
            pattern = r"(?i)\bscene\s+generation\s+complete\b"
            if re.search(pattern, scene.strip()):
                db["generating"] = False
                print("Scene generation complete. Stopping further scene generation.")
                break

            # Append the new scene to memory
            scenes.append({"role": "user", "content": scene})
            db["scenes"] = scenes
        socketio.emit('new_scene', {'scene_text': scene})
        
        # Generate dialogue and image description
        dialogue = dialogue_gen(scene)

        # Generate TTS audio in a separate thread
        def save_and_display_audio():
            audio_path = bhashini_tts(dialogue)
            if audio_path:
                with audio_lock:  # Ensure thread-safe updates to audio_paths
                    audio_paths.append(audio_path)
                print(f"Audio saved for Scene {scene_index}: {audio_path}")
                socketio.emit('new_audio', {'audio_url': audio_path})

        threading.Thread(target=save_and_display_audio).start()

        image_description = scene
        print(f"### Scene {scene_index}:")
        


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
                socketio.emit('new_image', {'image_url': image_path})

        threading.Thread(target=save_and_display_image).start()

        scene_index += 1
        with shelve.open("memory/story_memory") as db:
            db["scene_index"] = scene_index

    print("## Story Generation Complete. Waiting for images and audio to finish rendering...")
    print("Generated Images:")
    for img in image_paths:
        print(img)
    print("Generated Audio Files:")
    for audio in audio_paths:
        print(audio)

@app.route('/generate', methods=['POST'])
def generate():
    if request.method=='POST':
        # Get the prompt from the frontend
        data = request.get_json()
        prompt = data.get('prompt')
        socketio.start_background_task(target=generate_story, prompt=prompt)

        # Return a response to the frontend that generation has started
        return jsonify({'status': 'Generation started'})



@app.route("/test")
def test():
    return "It's working"    

if __name__ == "__main__":
    socketio.run(app, debug=True)