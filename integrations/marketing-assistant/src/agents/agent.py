import requests
from reel_creation_proto import UAgentResponse, UAgentResponseType, reel_creation_proto
import google.generativeai as genai
from uagents import Agent, Context, Protocol, Model
import os
import json
import time
from dotenv import load_dotenv
load_dotenv()

post_creation_protocol = Protocol("PostCreation")
SEED_PHRASE = os.environ.get("SEED_PHRASE")
APY_ACCESS_TOKEN = os.environ.get("APY_ACCESS_TOKEN")
IMAGE_CREATION_API_TOKEN = os.environ.get("IMAGE_CREATION_API_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
AGENT_MAILBOX_KEY = os.environ.get("AGENT_MAILBOX_KEY")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")

WEBSUMMARISER_API_BASE_URL = 'https://api.apyhub.com/extract/text/webpage?url='
WEBSUMMARISER_HEADERS = {
    'apy-token': f'{APY_ACCESS_TOKEN}'
}
IMAGE_CREATION_API_URL = "https://api-inference.huggingface.co/models/stablediffusionapi/crystal-clear-xlv1"
IMAGE_CREATION_HEADERS = {
    "Authorization": f'Bearer {IMAGE_CREATION_API_TOKEN}'
}
FIREBASE_API_URL = f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o"
API_KEY_PARAM = f"key={FIREBASE_API_KEY}"

print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")
localagent = Agent(
    name="Local Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

async def uploadToFirebaseStorage(file_data, destination_path, fileType):
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

async def createImageFromText(message, website):
    response = requests.post(IMAGE_CREATION_API_URL, headers=IMAGE_CREATION_HEADERS, json={"inputs": str(message)})
    website = website.replace('://','').replace('.','')
    fileName = website + '(())' + str(time.time()).replace('.','')
    url = await uploadToFirebaseStorage(response.content, f'{fileName}.png', 'image')
    return url

class PostCreation(Model):
    websiteUrl: str



def get_website_description ( websiteUrl):
    response = requests.get(WEBSUMMARISER_API_BASE_URL + websiteUrl, headers=WEBSUMMARISER_HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data['data']
    return ''

async def chat_with_gemini(message):
    genai.configure(api_key=f'{GEMINI_API_KEY}')
    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat(history=[])
    while True:
        user_message = message
        if user_message.lower() == 'quit':
            return "Exiting chat session."
        response = chat.send_message(user_message, stream=False)
        message = str(response.candidates[0].content.parts[0])
        data = json.loads(str(message[13:-7]).replace('\\n','').replace('\\','')[1:])
        return data

@post_creation_protocol.on_message(model=PostCreation, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: PostCreation):
    ctx.logger.info(f"Received message from {sender}.")

    try:
        data = ctx.storage.get(msg.websiteUrl)
        if(data is None):
            data = get_website_description(msg.websiteUrl)
            if(data is not None):
                ctx.storage.set(msg.websiteUrl, data)
        # else 

        # await ctx.send(sender, UAgentResponse(message='Crawled the website for description.',type=UAgentResponseType.FINAL))
        # await ctx.send(sender, UAgentResponse(message='Starting Work on creation of reels & posts.',type=UAgentResponseType.FINAL))
        reelsAndPostsData = ctx.storage.get('gemini-'+msg.websiteUrl)
        if(reelsAndPostsData is None):
            reelsAndPostsData = await chat_with_gemini('I want to create 2 reels and 5 illustrated Instagram posts for my company with website '+msg.websiteUrl+'. Can you go through this description of my company and write a description of 3 different reels and also give very detailed description of images to post along with a great professional caption with min 15 words. Also, make sure that the image in the post is not from the company product, as we have to feed this description to another service that generates the image form this image description. Also make sure image is a illustration and easy to produce.Please give this data in JSON string format which is convertable into python dict. Each reels should have minimum 7 scenes in it with background image described and text overlay given. Take this as a format of json in reels give 2 indexs background_image and text_overlay, in posts give 2 indexes caption and detailed description of image to post.  \n\n'+data)
            if(reelsAndPostsData is not None):
                ctx.storage.set('gemini-'+msg.websiteUrl, json.dumps(reelsAndPostsData))
        else:
            reelsAndPostsData = json.loads(reelsAndPostsData)
        final_message = 'Hello we have created a few posts from your website for you. Please have a look at them.\n\n'
        post = 1
        for item in reelsAndPostsData['posts']:
            url = await createImageFromText(item['detailed_description_of_image_to_post'],msg.websiteUrl)
            final_message += f'\nPost {post}\n'
            final_message += f'Image Link - <a href="{url}" target="_blank">Open Image</a>\n'
            final_message += f'Caption - '+item['caption']+'\n'
            post = post+1
        await ctx.send(sender, UAgentResponse(message=final_message,type=UAgentResponseType.FINAL))

    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))


localagent.include(post_creation_protocol)
localagent.include(reel_creation_proto)
localagent.run()

