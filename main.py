from quart import Quart, request, jsonify, render_template
from functions import use_vision64, use_vision64_from_url, encode_image, send_image_to_gpt4_vision, check_if_thread_exists, store_thread, remove_thread, send_animation_url, delete_message, transcribe_audio, transcribe_audio_from_url, run_assistant, handle_assistant_response, process_url, generate_response
# from bot2 import OPENAI_API_KEY, handle_assistant_response, encode_image, use_vision64
import openai
from openai import AsyncOpenAI
import requests
import base64
import os
import asyncio
import aiohttp
import shelve
from quart_compress import Compress


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VISION_ASSISTANT_ID = os.getenv('VISION_ASSISTANT_ID')
ASSISTANT2_ID = os.getenv('ASSISTANT2_ID')
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
    new_message = await run_assistant(thread, VISION_ASSISTANT_ID)
    print(new_message)
    return new_message


async def text_input(input):
    print(input)
    thread = await aclient.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": input
                    }
                ]
            }
        ]
    )
    new_message = await run_assistant(thread, ASSISTANT2_ID)
    print(new_message)
    return new_message


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


@app.route("/remove", methods=["POST"])
async def thread_remove():
    data = await request.get_json()
    usr_id = data.get('id')
    await remove_thread(usr_id)
    return 201


@app.route("/oga", methods=["POST"])
async def transcribe():
    data = await request.get_json()

    url = data.get('url')
    id = data.get('id')
    transcription = await transcribe_audio_from_url(url)
    # assistant_response = await handle_assistant_response(transcription)
    # assistant_response = await text_input(transcription)
    assistant_response = await generate_response(url, id, VISION_ASSISTANT_ID)

    response = {
        "transcription": transcription,
        "assistant_response": str(assistant_response)
    }

    return jsonify(response), 201


@app.route("/txt", methods=["POST"])
async def process_txt():
    print('txt triggered')
    data = await request.get_json()

    txt = data.get('txt')
    id = data.get('id')
    assistant_response = await generate_response(txt, id, VISION_ASSISTANT_ID)
    # vision1 = jsonify(vision).content

    return jsonify(assistant_response), 201


@app.route("/img", methods=["POST"])
async def process_image():
    print('img triggered')
    data = await request.get_json()

    url = data.get('url')
    vision = await use_vision64_from_url(url)
    # vision1 = jsonify(vision).content

    return jsonify(vision), 201


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


@app.route("/imggg", methods=["POST"])
async def image_proc():
    print('imGGG triggered')
    data = await request.get_json()
    url = data.get('url')
    id = data.get('id')
    print(data, url, id, TELETOKEN)
    result = await send_animation_url(TELETOKEN, id, file_url)
    message = result.get("result")
    mssg_id = message.get("message_id")

    vision = await process_url(url, id, VISION_ASSISTANT_ID)

    rr = await delete_message(TELETOKEN, id, mssg_id)
    return vision, 201

if __name__ == "__main__":
    # app.run(port=8080, debug=True)
    app.run(host="0.0.0.0", port=PORT, debug=True)
