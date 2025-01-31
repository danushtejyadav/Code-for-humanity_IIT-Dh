import os
import requests
import threading
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq
import shelve
import re

# Load environment variables
load_dotenv()

# Hugging Face API Keys
hugging_face_api_keys = [
    os.getenv("HUGGING_FACE_API_KEY_1"),
    os.getenv("HUGGING_FACE_API_KEY_2")
]
api_key_index = 0  # To track alternating API keys
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY1"))

# Create necessary folders
os.makedirs("memory", exist_ok=True)
os.makedirs("s1", exist_ok=True)

def get_next_api_key():
    global api_key_index
    api_key = hugging_face_api_keys[api_key_index]
    api_key_index = (api_key_index + 1) % len(hugging_face_api_keys)
    return api_key

# Image Generation Function
def image_gen(prompt, scene_index):
    headers = {"Authorization": f"Bearer {get_next_api_key()}"}
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
    sys_msg = "Generate a short story based on the given prompt."
    convo = [{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# Scene Generation
def scene_generator(full_story_text, memory):
    sys_msg = (
        "You are given a full short story. Generate one scene at a time based on the story. "
        "If the story is complete, return 'Scene generation complete'."
    )
    convo = memory + [{"role": "system", "content": sys_msg}, {"role": "user", "content": full_story_text}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# Dialogue Generation
def dialogue_gen(scene):
    sys_msg = "Generate a dialogue for one character based on the given scene."
    convo = [{"role": "system", "content": sys_msg}, {"role": "user", "content": scene}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# Image Prompt Generation
def image_prompt_gen(scene):
    sys_msg = (
        "You are given a scene description. Generate a detailed and descriptive prompt for an image generation model. "
        "Include specific visual details like colors, objects, and actions."
        "The prompt should be animatic-friendly."
    )
    convo = [{"role": "system", "content": sys_msg}, {"role": "user", "content": scene}]
    chat_completion = groq_client.chat.completions.create(messages=convo, model="llama3-70b-8192")
    return chat_completion.choices[0].message.content

# Main Story Generation Function
def generate_story(user_prompt):
    # Initialize memory using shelve
    with shelve.open("memory/story_memory") as db:
        if "full_story" not in db:
            db["full_story"] = full_story(user_prompt)
            db["scenes"] = []
            db["scene_index"] = 1
            db["images"] = []
            db["generating"] = True

        full_story_text = db["full_story"]
        scenes = db["scenes"]
        scene_index = db["scene_index"]
        images = db["images"]
        generating = db["generating"]

    print("## Full Story:")
    print(full_story_text)

    # Scene Generation Loop
    while generating:
        with shelve.open("memory/story_memory") as db:
            scene = scene_generator(full_story_text, db["scenes"])
            pattern =r"(?i)\bscene generation complete(d?)\b" 
            if re.fullmatch(pattern, scene.strip()):
                db["generating"] = False
                break

            # Append the new scene to memory
            scenes.append({"role": "user", "content": scene})
            db["scenes"] = scenes

        # Generate dialogue and image description
        dialogue = dialogue_gen(scene)
        image_description = scene

        print(f"### Scene {scene_index}:")
        print(scene)
        print(f"**Dialogue:** {dialogue}")

        # Generate image prompt
        image_prompt = image_prompt_gen(image_description)

        # Generate image in a separate thread
        def save_and_display_image():
            image_path = image_gen(image_prompt, scene_index)
            if image_path:
                with shelve.open("memory/story_memory") as db:
                    images = db["images"]
                    images.append(image_path)
                    db["images"] = images
                print(f"Image saved for Scene {scene_index}: {image_path}")

        threading.Thread(target=save_and_display_image).start()

        scene_index += 1
        with shelve.open("memory/story_memory") as db:
            db["scene_index"] = scene_index

    print("## Story Generation Complete. Waiting for images to finish rendering...")

# Main Function
def main():
    user_prompt = input("Enter the topic for the story: ")
    if user_prompt:
        generate_story(user_prompt)

if __name__ == "__main__":
    main()