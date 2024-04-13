import requests
import os
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol, Model
from elevenlabs import save,VoiceSettings,Voice
from elevenlabs.client import ElevenLabs
import time
from dotenv import load_dotenv
from moviepy import editor
import json
import textwrap
load_dotenv()

reel_creation_proto = Protocol("ReelCreation")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
print(ELEVENLABS_API_KEY)

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
IMAGE_CREATION_API_TOKEN = os.environ.get("IMAGE_CREATION_API_TOKEN")
IMAGE_CREATION_API_URL = "https://api-inference.huggingface.co/models/stablediffusionapi/crystal-clear-xlv1"
IMAGE_CREATION_HEADERS = {
    "Authorization": f'Bearer {IMAGE_CREATION_API_TOKEN}'
}
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")
FIREBASE_API_URL = f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o"
API_KEY_PARAM = f"key={FIREBASE_API_KEY}"
ELEVEN_VOICE_ID = os.environ.get("ELEVEN_VOICE_ID")

class ReelCreation(Model):
    websiteUrl: str


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

async def createImageFromText(message, textOverlay, fileName):
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
    image.save(f'../assets/images/{fileName}.png')

async def createScript(script, reelId):
    audio = client.generate(
        text=script,
        voice=Voice(
            voice_id=f'{ELEVEN_VOICE_ID}',
            settings=VoiceSettings(stability=1, similarity_boost=1, style=1, use_speaker_boost=True)
        )
    )
    save(audio,f"../assets/audio/{reelId}.mp3")

@reel_creation_proto.on_message(model=ReelCreation, replies={UAgentResponse})
async def reel_creation(ctx: Context, sender: str, msg: ReelCreation):
    ctx.logger.info(f"Received booking request from {sender}")
    ctx.storage.set('s','ss')
    try:
        reelsAndPostsData = ctx.storage.get('gemini-'+msg.websiteUrl)
        if(reelsAndPostsData is not None):
            reelsAndPostsData = json.loads(reelsAndPostsData)
        reels = reelsAndPostsData["reels"]
        print(reels)
        for reel in reels:
            reelId = str(time.time()).replace('.','')
            script = " ".join(scene["text_overlay"] for scene in reel["scenes"])
            await createScript(script, reelId)
            serial_of_image = 1
            image_list = list()
            for scene in reel['scenes']:
                await createImageFromText(scene['background_image'], scene['text_overlay'], f'{reelId}-{serial_of_image}')
                serial_of_image = serial_of_image+1
                image_list.append(Image.open(f'../assets/images/{reelId}-{serial_of_image}.png'))
            length_audio = audio_length
            duration = int(length_audio / len(image_list)) * 1000
            image_list[0].save(f'../assets/images/{reelId}.gif',
                            save_all=True,
                            append_images=image_list[1:],
                            duration=duration
                        )
            video = editor.VideoFileClip(f'../assets/images/{reelId}.gif')
            audio = editor.AudioFileClip(f'../assets/audio/{reelId}.mp3')
            final_video = video.set_audio(audio)
            final_video.set_fps(60)
            final_video.write_videofile(full_video_path)
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Thanks for choosing an option - {option[msg.user_response]}.",
                type=UAgentResponseType.FINAL,
                request_id=msg.request_id
            )
        )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender,
            UAgentResponse(
                message=str(exc),
                type=UAgentResponseType.ERROR
            )
        )


