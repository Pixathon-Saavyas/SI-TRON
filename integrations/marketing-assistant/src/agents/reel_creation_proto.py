import requests
import os
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol, Model
from elevenlabs import save,VoiceSettings,Voice
from elevenlabs.client import ElevenLabs

reel_creation_proto = Protocol("ReelCreation")
client = ElevenLabs(
  api_key=os.environ.get("elevenLabs_api_key"), # Defaults to ELEVEN_API_KEY
)
class ReelCreation(Model):
    websiteUrl: str

@reel_creation_proto.on_message(model=ReelCreation, replies={UAgentResponse})
async def booking_handler(ctx: Context, sender: str, msg: ReelCreation):
    ctx.logger.info(f"Received booking request from {sender}")
    try:
        option = ctx.storage.get(msg.request_id)
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

def textToAudio (script):
    print("Reached 1")
    audio = client.generate(
    text=script,
    voice=Voice(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        settings=VoiceSettings(stability=1, similarity_boost=1, style=1, use_speaker_boost=True)
        )
    )
    print("Reached 2")
    save(audio,"my-file.mp3")
    return("Done!!")

def reelCreation(reel_description):
    try:
        scenes = reel_description["scenes"]
        script = " ".join(scene["text_overlay"] for scene in scenes)
        result = textToAudio(script)
        print(result)
    except Exception as exc:
        print(exc)
    

reelCreation(reelDescription)

