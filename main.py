from quart import Quart, request, jsonify, render_template
from functions import use_vision64, use_vision64_from_url, encode_image, send_image_to_gpt4_vision
# from bot2 import OPENAI_API_KEY, handle_assistant_response, encode_image, use_vision64
import openai
from openai import AsyncOpenAI
import requests
import base64
import os
import asyncio
import aiohttp
from quart_compress import Compress


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VISION_ASSISTANT_ID = os.getenv('VISION_ASSISTANT_ID')
client = openai.OpenAI(api_key=OPENAI_API_KEY)
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai.api_key = OPENAI_API_KEY

PORT = os.getenv('PORT')           # get the port generated by railway
TELETOKEN = os.getenv('TELEBOT')
file_url = "https://github.com/HollowTwat/quart-test/blob/main/hmm.gif?raw=true"

# app = Quart(__name__)
app = Quart(__name__, static_url_path='/static')
# required to get a visitors IP through railway
app.config["SESSION_REVERSE_PROXY"] = True
Compress(app)


@app.errorhandler(404)
async def handle_not_found(e):
    return '<h1>😦</h1><b>404</b> Not found.<p><a href="/">return</a>'


async def send_animation_url(token, chat_id, animation_url):
    url = f"https://api.telegram.org/bot{token}/sendAnimation"
    data = {
        'chat_id': chat_id,
        'animation': animation_url
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            return await response.json()


async def delete_message(token, chat_id, message_id):
    url = f"https://api.telegram.org/bot{token}/deleteMessage"
    data = {
        'chat_id': chat_id,
        'message_id': message_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            result = await response.json()
            return result
            

async def handle_img_link(link):
    print(link)
    thread = await aclient.beta.threads.create(
        messages=[

            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": link},
                    },]
            },
        ]
    )
    new_message = await run_assistant(thread)
    print(new_message)
    return new_message


async def run_assistant(thread):
    assistant = await aclient.beta.assistants.retrieve(VISION_ASSISTANT_ID)
    run = await aclient.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    while run.status != "completed":
        await asyncio.sleep(1.5)
        run = await aclient.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id)

    messages = await aclient.beta.threads.messages.list(thread_id=thread.id)
    latest_mssg = messages.data[0].content[0].text.value
    print(f"generated: {latest_mssg}")
    return latest_mssg


async def handle_assistant_response(prompt):
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()


async def transcribe_audio(file_path):
    with open(file_path, 'rb') as audio_file:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return response.text


async def transcribe_audio_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        temp_file_path = 'temp_audio.ogg'
        with open(temp_file_path, 'wb') as f:
            f.write(response.content)
        transcription = await transcribe_audio(temp_file_path)
        return transcription
    else:
        raise Exception(f"Failed to fetch audio from URL: {response.status}")


@app.route("/")
async def index() -> str:
    return await render_template("index.html")


@app.route("/get-user/<user_id>")
async def get_user(user_id):
    user_data = {
        "user_id": user_id,
        "name": "John",
        "email": "example@example.com"
    }

    extra = request.args.get("extra")
    if extra:
        user_data["extra"] = extra

    return jsonify(user_data), 200


@app.route("/oga", methods=["POST"])
async def transcribe():
    data = await request.get_json()

    url = data.get('url')
    transcription = await transcribe_audio_from_url(url)
    assistant_response = await handle_assistant_response(transcription)

    response = {
        "transcription": transcription,
        "assistant_response": assistant_response
    }

    return jsonify(response), 201


@app.route("/img", methods=["POST"])
async def process_image():
    print('img triggered')
    data = await request.get_json()

    url = data.get('url')
    vision = await use_vision64_from_url(url)
    # vision1 = jsonify(vision).content

    return jsonify(vision), 201

@app.route("/img2", methods=["POST"])
async def process_url():
    print('imG2 triggered')
    data = await request.get_json()
    url = data.get('url')
    print(data, url, id, TELETOKEN)
    vision = await handle_img_link(url)
    print(vision)
    return vision, 201
    
@app.route("/imgg", methods=["POST"])
async def process_url():
    print('imGG triggered')
    data = await request.get_json()
    url = data.get('url')
    id = data.get('id')
    print(data, url, id, TELETOKEN)
    result = await send_animation_url(TELETOKEN, id, file_url)
    # parsable_result = result.json()
    message = result.get("result")
    mssg_id = message.get("message_id")
    vision = await handle_img_link(url)
    print(vision)
    rr = await delete_message(TELETOKEN, id, mssg_id)
    return vision, 201

if __name__ == "__main__":
    # app.run(port=8080, debug=True)
    app.run(host="0.0.0.0", port=PORT, debug=True)
