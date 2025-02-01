 IntelliQuery

 🚀 Overview

IntelliQuery is a Generative AI-powered platform that turns complex topics into engaging, interactive videos. It uses real-world examples and customized visual aids in multiple languages to make learning more intuitive and fun.

 🛠 How It Works

1. User Input - The user provides a topic or prompt.
2. Story Generation - The story generation agent understands the query and creates a compelling storyboard.
3. Image Prompter - This agent prompts the Flux AI model to generate consistent and relevant scenes.
4. Dialogue Generation - This agent creates dialogues that will be converted into audio from a narrative perspective.
5. Image Creation - Flux AI generates images based on the given storyboard.
6. Video Compilation - All elements are combined into an engaging educational video.
7. Web Search & Summarization - If a user wants to explore real-world articles or key topics that are boring to read, IntelliQuery uses NewsAPI to search the web, scrapes relevant text and images, summarizes the content using LLM, and compiles a video with visuals and audio.

 🔥 Key Features

- Automated Story Generation - Converts any topic into a structured story.
- AI-Powered Image & Audio Generation - Enhances learning with visuals and sound.
- Interactive Video Compilation - Creates videos from text-based prompts.
- Multilingual Support - Uses Bhashini API for multiple languages.
- Powered by Open-Source AI - Utilizes LLaMA 70B and agent-based workflows.
- Real-World Content Summarization - Extracts, summarizes, and converts web articles into interactive videos.

 🛠 Tech Stack

- Backend: Python, Flask
- Frontend: HTML, CSS, JavaScript
- AI Models: LLaMA 70B, Groq for LLM
- Multilinguality: Bhashini API, Deepgram
- Web Scraping & Search: NewsAPI, Web Scraping Tools
- Version Control: GitHub

 🏗 Installation & Setup

1. Clone the repository:
   bash
   >>git clone https://github.com/your-repo/intelliquery.git
   >>cd intelliquery
   
2. Install dependencies:
   bash
   >>pip install -r requirements.txt
   
3. Start the Flask server:
   bash
   >>python app.py
   
4. Open your browser and visit http://localhost:5000.

 📌 Usage

- Enter a topic or prompt.
- IntelliQuery will generate a structured story and break it into scenes.
- AI will generate images and audio for each scene.
- The final video will be compiled and ready for viewing.
- For real-world topics, IntelliQuery will fetch relevant articles, summarize them, and create a video.

