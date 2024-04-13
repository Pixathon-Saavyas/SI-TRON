from mutagen.mp3 import MP3
from PIL import Image, ImageDraw, ImageFont
import io
from pathlib import Path
from moviepy import editor
import os 
import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol, Model
from elevenlabs import save,VoiceSettings,Voice
from elevenlabs.client import ElevenLabs
import google.generativeai as genai
from uagents import Agent, Context, Protocol, Model
import json
import time
from dotenv import load_dotenv
import textwrap
load_dotenv()

reel_creation_proto = Protocol("ReelCreation")
client = ElevenLabs(
  api_key=os.environ.get("elevenLabs_api_key"), # Defaults to ELEVEN_API_KEY
)
# Reading in the mp3 that we got from gTTS
IMAGE_CREATION_API_TOKEN = os.environ.get("IMAGE_CREATION_API_TOKEN")
IMAGE_CREATION_API_URL = "https://api-inference.huggingface.co/models/stablediffusionapi/crystal-clear-xlv1"
IMAGE_CREATION_HEADERS = {
    "Authorization": f'Bearer {IMAGE_CREATION_API_TOKEN}'
}
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")
FIREBASE_API_URL = f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o"
API_KEY_PARAM = f"key={FIREBASE_API_KEY}"
reelDescription = {
    "title": "Boost your sales with mobile apps!",
    "scenes": [
    {
        "background_image": "A busy city street with people walking and holding shopping bags",
        "text_overlay": "Struggling to convert website visitors into sales?"
    },
    {
        "background_image": "Close-up shot of a smartphone with a shopping cart icon on the screen",
        "text_overlay": "Mobile apps have the lowest cart abandonment rate!"
    },
    {
        "background_image": "Illustration of a line graph showing increasing sales",
        "text_overlay": "See a 3x boost in conversions with your own app!"
    },
    {
        "background_image": "A split screen showing a person frustrated at a computer and a person happily shopping on their phone",
        "text_overlay": "Apptile makes creating a mobile app easy - no coding required!"
    },
    {
        "background_image": "Showcase of various customizable app tile designs on a phone screen",
        "text_overlay": "Design a beautiful app that reflects your brand."
    },
    {
        "background_image": "Close-up shot of a person smiling while using a phone app",
        "text_overlay": "Increase customer engagement and loyalty."
    },
    {
        "background_image": "Apptile logo",
        "text_overlay": "Get started today and see results! #mobileapp #ecommerce #conversionrate #apptile"
    }
    ]
}
scenes = reelDescription["scenes"]
script = " ".join(scene["text_overlay"] for scene in scenes)
audio = client.generate(
text=script,
voice=Voice(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    settings=VoiceSettings(stability=1, similarity_boost=1, style=1, use_speaker_boost=True)
    )
)
save(audio,"my-file.mp3")

def uploadToFirebaseStorage(file_data, destination_path, fileType):
    upload_url = f"{FIREBASE_API_URL}/{destination_path}?{API_KEY_PARAM}"
    contentType = "image/png"
    if (fileType == 'video'): 
        contentType = "video/mp4"
    headers = {"Content-Type": f'{contentType}'}
    print(upload_url)
    response = requests.post(upload_url, headers=headers, data=file_data)

    if response.status_code == 200:
        download_url = response.json().get("downloadTokens", "")
        firebase_url = f"{FIREBASE_API_URL}/{destination_path}?alt=media&token={download_url}"
        return firebase_url
    else:
        print("Error uploading to Firebase Storage:", response.content)
        return None
serial_of_image = 1
def createImageFromText(message, textOverlay, serialImage):
    response = requests.post(IMAGE_CREATION_API_URL, headers=IMAGE_CREATION_HEADERS, json={"inputs": str(message)})
    fileName = str(time.time()).replace('.','')
    image = Image.open(io.BytesIO(response.content))
    title_font = ImageFont.truetype('./fonts/OpenSans-Bold.ttf', 50)
    image_editable = ImageDraw.Draw(image)
    image_width, image_height = image.size
    y_text = 200
    lines = textwrap.wrap(textOverlay, width=40)
    for line in lines:
        line_width, line_height = title_font.getsize(line)
        image_editable.text(((image_width - line_width) / 2, y_text), 
                  line, font=title_font, fill=(237, 230, 211))
        y_text += line_height
    image.save(f'./images/{serialImage}.png')
for item in reelDescription['scenes']:
    print(item['background_image'])
    url = createImageFromText(item['background_image'], item['text_overlay'], serial_of_image)
    serial_of_image += 1
    print(url)
folder_path = './images'
audio_path = "my-file.mp3"
full_video_path = "AmazonRedShift.mp4"

# Globbing the images and Stitching it to for the gif
song = MP3(audio_path)
audio_length = round(song.info.length)
audio_length

path_images = Path(folder_path)

images = list(path_images.glob('*.png'))

image_list = list()

for image_name in images:
    image = Image.open(image_name).resize((800, 800), Image.LANCZOS)
    image_list.append(image)
    
#Checking Audio length

length_audio = audio_length
duration = int(length_audio / len(image_list)) * 1000
print(duration)

#Creating Gif

image_list[0].save(os.path.join(folder_path,"temp.gif"),
                   save_all=True,
                   append_images=image_list[1:],
                   duration=duration)

# Creating the video using the gif and the audio file

video = editor.VideoFileClip(os.path.join(folder_path,"temp.gif"))
print('done video')

audio = editor.AudioFileClip(audio_path)
print('done audio')

final_video = video.set_audio(audio)
print('Set Audio and writing')

final_video.set_fps(60)

final_video.write_videofile(full_video_path)

os.system('rm -rf ./images/*')