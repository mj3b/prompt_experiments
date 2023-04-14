# This Python script generates a narrated video that combines AI-generated images in the style Wassily Kandinsky with an AI-generated voiceover. The story follows Eleanor, a watchmaker, and her peculiar cat Chronos, as they experience a magical journey through time. The images are generated using OpenAI's DALL-E API, and the narration is synthesized using Google Cloud's Text-to-Speech API. Feel free to tinker with your own prompts -- and show us what you make with it!

import os
import datetime
from google.cloud import texttospeech
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import requests
from PIL import Image

url = "https://api.openai.com/v1/images/generations"

def save_image_from_response(response, filename):
    with open(filename, "wb") as f:
        f.write(response.content)

def split_text_into_chunks(text, num_chunks):
    sentences = [s.strip() for s in text.split('.') if s.strip()]  # Remove empty sentences
    num_sentences = len(sentences)
    base_chunk_size = num_sentences // num_chunks
    extra_sentences = num_sentences % num_chunks

    chunks = []
    start = 0

    for i in range(num_chunks):
        chunk_size = base_chunk_size + (1 if i < extra_sentences else 0)
        end = start + chunk_size
        chunk = '. '.join(sentences[start:end])
        chunks.append(chunk)
        start = end

    return chunks

# -------------------------- Hard-coded prompts --------------------------
prompt_list = [
    "Once, in a quaint little village, there lived a watchmaker named Eleanor.",
    "Eleanor was renowned for her unmatched skill in crafting timepieces that transcended the ordinary, each a testament to her artistry and precision.",
    "In her workshop, amidst the delicate gears and springs, a peculiar cat named Chronos kept her company.",
    "One stormy night, as the rain pattered against the windows, Eleanor unveiled her masterpiece: a pocket watch adorned with intricate engravings that seemed to dance in the dim candlelight.",
    "As she held it, she noticed Chronos gazing intently at the watch's rhythmic ticking.",
    "Suddenly, Chronos pounced, tapping the watch with his paw, and the world froze.",
    "Time itself seemed to bend, transporting Eleanor and her cat to moments of joy, love, and loss from her past.",
    "In the silence between the seconds, she discovered a newfound appreciation for the beauty of time's fleeting nature.",
    "Eleanor and Chronos returned to the workshop as the watch sprang back to life.",
    "With the memories of her journey still fresh, Eleanor vowed to create timepieces that celebrated life's fleeting moments.",
    "And so, a whisker in time had changed the course of the watchmaker's life forever."
]

text = ". ".join(prompt_list)

# -------------------------- Text-to-Speech using Google Cloud API --------------------------
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "[/PATH/TO/YOUR/CREDENTIALS.json]"
client = texttospeech.TextToSpeechClient()

voice = texttospeech.VoiceSelectionParams(
    language_code="en-gb",
    ssml_gender=texttospeech.SsmlVoiceGender.MALE,
    name="en-GB-Neural2-D"
)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=1.0,
    pitch=0.0,
)

# Generate audio
synthesis_input = texttospeech.SynthesisInput(text=text)
response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

# Save audio
audio_filename = f"audio_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}.mp3"
with open(audio_filename, "wb") as out:
    out.write(response.audio_content)
    out.flush()
    os.fsync(out.fileno())

# -------------------------- Image Generation using DALL-E API --------------------------
api_key = "[YOUR_OPENAI_API_KEY"
url = "https://api.openai.com/v1/images/generations"
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

# Hard-coded prompts
prompt_list = [
    "A quaint little village with a watchmaker's workshop and Eleanor the watchmaker.",
    "Eleanor, the watchmaker, crafting intricate timepieces in her workshop, surrounded by delicate gears and springs.",
    "A peculiar cat, keeping Eleanor (who is a watchmaker) company in the workshop.",
    "A stormy night with rain pattering against the windows of Eleanor the watchmaker's workshop.",
    "Eleanor the watchmaker unveiling her masterpiece, a pocket watch adorned with intricate engravings, in the dim candlelight.",
    "A peculiar cat gazing intently at the rhythmic ticking of an intricately-engraved pocket watch.",
    "A peculiar cat tapping an intricately-engraved pocket watch with his paw, freezing the world around the cat and Eleanor the Watchmaker.",
    "Eleanor (a watchmaker) and her peculiar cat in an ethereal realm, witnessing the ebb and flow of Eleanor's life.",
    "Eleanor the Watchmaker's mother's tender embrace and her father's guiding hand, as memories within the tapestry of time.",
    "Eleanor and her peculiar cat back in the workshop, crafting timepieces that capture the essence of life's fleeting moments."
]

image_filenames = []

for i, prompt in enumerate(prompt_list):
    if not prompt:
        continue

    # Generate image
    data = {
        "prompt": f"Depicting a scene of Eleanor the watchmaker and/or her cat, in the style Wassily Kandinsky: {prompt}",
        "n": 1,
        "size": "1024x1024",
        "response_format": "url"
    }

    response = requests.post(url, headers=headers, json=data)

    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Failed to decode JSON response for chunk {i}.")
        continue

    print(f"Response JSON: {response_json}")
    response.raise_for_status()

    if response_json["data"]:
        image_url = response_json["data"][0]["url"]

        # Save image
        image_response = requests.get(image_url)
        image_filename = f"image_{i}_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        save_image_from_response(image_response, image_filename)
        image_filenames.append(image_filename)
    else:
        print(f"Image generation failed for chunk {i}: {response_json['error']['message']}")

# -------------------------- Video Generation using MoviePy --------------------------

audio = AudioFileClip(audio_filename, fps=44100)

# Check if the image_clips list is empty and raise an error if it is
if not image_filenames:
    raise ValueError("No images were generated. Please check your API calls and API key.")
    
# Create image clips and set their durations
num_images = len(image_filenames)
image_clips = [ImageClip(image_filename).set_duration(audio.duration / num_images) for image_filename in image_filenames]

# Concatenate image clips
final_clip = concatenate_videoclips(image_clips)

# Save the final video
output_video_filename = f"final_video_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}.mp4"
final_clip.set_audio(audio).write_videofile(output_video_filename, fps=24, codec="libx264", audio_codec="aac")
