import requests
from reel_creation_proto import UAgentResponse, UAgentResponseType, reel_creation_proto
import google.generativeai as genai
from uagents import Agent, Context, Protocol, Model
import os
import json
from dotenv import load_dotenv
load_dotenv()

post_creation_protocol = Protocol("PostCreation")
SEED_PHRASE = os.environ.get("SEED_PHRASE")
APY_ACCESS_TOKEN = os.environ.get("APY_ACCESS_TOKEN")
IMAGE_CREATION_API_TOKEN = os.environ.get("IMAGE_CREATION_API_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
AGENT_MAILBOX_KEY = os.environ.get("AGENT_MAILBOX_KEY")

WEBSUMMARISER_API_BASE_URL = 'https://api.apyhub.com/extract/text/webpage?url='
WEBSUMMARISER_HEADERS = {
    'apy-token': f'{APY_ACCESS_TOKEN}'
}
IMAGE_CREATION_API_URL = "https://api-inference.huggingface.co/models/stablediffusionapi/crystal-clear-xlv1"
IMAGE_CREATION_HEADERS = {
    "Authorization": f'Bearer {IMAGE_CREATION_API_TOKEN}'
}
print(SEED_PHRASE)
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")
localagent = Agent(
    name="Local Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

# def query(payload):
# 	response = requests.post(API_URL, headers=headers, json=payload)
# 	return response.content
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
            reelsAndPostsData = await chat_with_gemini('I want to create 3 reels and 3 illustrated Instagram posts for my company with website '+msg.websiteUrl+'. Can you go through this description of my company and write a description of 3 different reels and also give very detailed description of images to post along with a caption. Also, make sure that the image in the post is not from the company product, as we have to feed this description to another service that generates the image form this image description. Also make sure image is a illustration and easy to produce.Please give this data in JSON string format which is convertable into python dict. Each reels should have minimum 7 scenes in it with background image described and text overlay given.\n\n'+data)
            if(reelsAndPostsData is not None):
                ctx.storage.set('gemini-'+msg.websiteUrl, json.dumps(reelsAndPostsData))
        else:
            reelsAndPostsData = json.loads(reelsAndPostsData)
        
        print(reelsAndPostsData['posts'].length)
        message = "Generating posts<b>WHAT A GREAT MAN</b>"
        await ctx.send(sender, UAgentResponse(message=message,type=UAgentResponseType.FINAL))

    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))

# posts = [{'description': 'Image 1: EduWol - Empowering Students, Transforming Education', 'image': {'illustration': 'A vibrant illustration of students and teachers engaged in a dynamic learning environment, surrounded by books, technology, and a supportive community.'}, 'caption': "At EduWol, we believe that every student deserves the opportunity to excel. Our educational ecosystem empowers students with interactive learning experiences, expert mentorship, and tailored courses, fostering collaboration, innovation, and success. Join us and let's transform education together! #EduWol #EducationRevolution #EmpoweringStudents"}, {'description': 'Image 2: EduWol - The Bridge to Your Educational Dreams', 'image': {'illustration': 'An artistic representation of a bridge connecting a group of students to their educational aspirations, with EduWol as the guiding light.'}, 'caption': "Your educational journey doesn't have to be a solitary path. With EduWol as your partner, you have a bridge to your dreams. Our comprehensive courses, expert guidance, and supportive community will help you navigate your academic pursuits and reach new heights. Let's walk the path of success together! #EduWol #BridgeToEducation #DreamBuilders"}, {'description': 'Image 3: EduWol - Igniting the Spark of Discovery', 'image': {'illustration': 'A captivating illustration of a student surrounded by floating books, representing the boundless possibilities of knowledge and the spark of discovery.'}, 'caption': "At EduWol, we believe that learning should be an exhilarating adventure. Our platform ignites the spark of discovery, providing a world of knowledge at your fingertips. Dive into our interactive lessons, engage with expert mentors, and let your curiosity lead the way. Together, let's unlock the boundless potential within you! #EduWol #SparkOfDiscovery #LimitlessLearning"}]
# createImageFromText(posts[0]["description"]+'. '+posts[0]["image"]["illustration"])


localagent.include(post_creation_protocol)
localagent.include(reel_creation_proto)
localagent.run()

