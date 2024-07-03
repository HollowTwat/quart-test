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
import shelve

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VISION_ASSISTANT_ID = os.getenv('VISION_ASSISTANT_ID')
ASSISTANT2_ID = os.getenv('ASSISTANT2_ID')
client = openai.OpenAI(api_key=OPENAI_API_KEY)
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai.api_key = OPENAI_API_KEY


async def process_url(url, usr_id):
    thread_id = await check_if_thread_exists(usr_id)

    if thread_id is None:
        print(f"Creating new thread for {usr_id}")
        thread = await client.beta.threads.create()
        await store_thread(usr_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread {usr_id}")
        thread = await client.beta.threads.retrieve(thread_id)
    print(url)
    thread = await client.beta.threads.create(
        messages=[

            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": url},
                    },]
            },
        ]
    )
    await store_thread(usr_id, thread.id)

    new_message = await run_assistant(thread)


async def check_if_thread_exists(usr_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(usr_id, None)


async def store_thread(usr_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[usr_id] = thread_id


async def remove_thread(user_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        if user_id in threads_shelf:
            del threads_shelf[user_id]
            print("thread_id deleted")
        else:
            print("didn't delete, not there")


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


async def run_assistant(thread, assistant):
    assistant = await aclient.beta.assistants.retrieve(assistant)
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


async def use_vision64(file_path):

    base64_image = encode_image(file_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Что изображено на этой картинке"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 750
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    response_json = response.json()
    print(response_json)
    content = response_json['choices'][0]['message']['content']
    return content


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


async def send_image_to_gpt4_vision(image_path):
    with open(image_path, 'rb') as image_file:
        response = client.embeddings.create(
            assistant_id=GPT4_VISION_ASSISTANT_ID,
            file=image_file
            # model="dall-e"  # Replace with the correct model name if needed
        )
    return response['choices'][0]['text']


async def use_vision64_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        temp_file_path = 'temp_img.jpg'
        with open(temp_file_path, 'wb') as f:
            f.write(response.content)
        return await use_vision64(temp_file_path)
    else:
        raise Exception(
            f"Failed to fetch video from URL: {response.status_code}")


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


async def generate_response(message_body, usr_id):
    thread_id = await check_if_thread_exists(usr_id)
    print(message_body, thread_id)

    if thread_id is None:
        print(f"Creating new thread for {usr_id}")
        thread = await client.beta.threads.create()
        await store_thread(usr_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread {usr_id}")
        thread = await client.beta.threads.retrieve(thread_id)

    message = await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )
    print(message)

    new_message = await run_assistant(thread)
    return new_message
