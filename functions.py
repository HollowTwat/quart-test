from quart import Quart, request, jsonify, render_template
import openai
from openai import AsyncOpenAI
import requests
import base64
import os
import asyncio
import aiohttp
import shelve
import re

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VISION_ASSISTANT_ID = os.getenv('VISION_ASSISTANT_ID')
CITY_ASSISTANT_ID = os.getenv('CITY_ASSISTANT_ID')
ASSISTANT2_ID = os.getenv('ASSISTANT2_ID')
YAPP_SESH_ASSISTANT_ID = os.getenv('YAPP_SESH_ASSISTANT_ID')
client = openai.OpenAI(api_key=OPENAI_API_KEY)
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai.api_key = OPENAI_API_KEY
TELETOKEN_2 = os.getenv('TELEBOT_2')
bug_channel = "-1002345895875"




async def remove_reference(input_string):
    # Use regular expression to match text between 【 and 】, including the symbols
    result = re.sub(r'【.*?】', '', input_string)
    result1 = result.replace("<br>", "\n")
    return result1

async def generate_response(message_body, usr_id, assistant):
    thread_id = await check_if_thread_exists(usr_id)
    print(message_body, thread_id)

    if thread_id is None:
        print(f"Creating new thread for {usr_id}")
        thread = await aclient.beta.threads.create()
        await store_thread(usr_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread {usr_id}")
        thread = await aclient.beta.threads.retrieve(thread_id)

    print(thread_id)
    message = await aclient.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )
    print(f"message: {message}")

    new_message = await run_assistant(thread, assistant)
    return new_message


async def process_url(url, usr_id, assistant):
    thread_id = await check_if_thread_exists(usr_id)

    if thread_id is None:
        print(f"Creating new thread for {usr_id}")
        thread = await aclient.beta.threads.create()
        await store_thread(usr_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread {usr_id}")
        thread = await aclient.beta.threads.retrieve(thread_id)
    print(url)
    thread = await aclient.beta.threads.create(
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

    new_message = await run_assistant(thread, assistant)

    return new_message


async def process_url_etik(url, allergies, usr_id, assistant):

    thread = await aclient.beta.threads.create(
        messages=[

            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": url},
                    },
                {
                    "type": "text",
                    "text": f"У пользователя есть алергии на {allergies}"
                },]
            },
        ]
    )

    new_message = await run_assistant(thread, assistant)
    print(new_message)

    return new_message


async def check_if_thread_exists(usr_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(usr_id, None)


async def check_if_yapp_thread_exists(usr_id):
    with shelve.open("yapp_db") as threads_shelf:
        return threads_shelf.get(usr_id, None)


async def store_thread(usr_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[usr_id] = thread_id


async def store_yapp_thread(usr_id, thread_id):
    with shelve.open("yapp_db", writeback=True) as threads_shelf:
        threads_shelf[usr_id] = thread_id


async def remove_thread(user_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        if user_id in threads_shelf:
            del threads_shelf[user_id]
            print("thread_id deleted")
        else:
            print("didn't delete, not there")

async def remove_yapp_thread(user_id):
    with shelve.open("yapp_db", writeback=True) as threads_shelf:
        if user_id in threads_shelf:
            del threads_shelf[user_id]
            print("thread_id deleted")
        else:
            print("didn't delete, not there")


async def check_if_rec_thread_exists(usr_id):
    with shelve.open("rec_db") as threads_shelf:
        return threads_shelf.get(usr_id, None)


async def store_rec_thread(usr_id, thread_id):
    with shelve.open("rec_db", writeback=True) as threads_shelf:
        threads_shelf[usr_id] = thread_id


async def remove_rec_thread(user_id):
    with shelve.open("rec_db", writeback=True) as threads_shelf:
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


async def send_sticker(token, chat_id, sticker_id):
    url = f"https://api.telegram.org/bot{token}/sendSticker"
    data = {
        'chat_id': chat_id,
        "sticker": sticker_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            return await response.json()


async def send_mssg(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text
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
    try:
        print("run_assistant hit")
        assistant = await aclient.beta.assistants.retrieve(assistant)
        run = await aclient.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )
    
        while run.status != "completed":
            if run.status == "failed":
                messages = await aclient.beta.threads.messages.list(thread_id=thread.id)
                raise Exception(
                    f"Run failed with status: {run.status} and generated {messages.data[0]} and also {run.failed_at} and {run.incomplete_details}")

            print(run.status)
            await asyncio.sleep(1.5)
            run = await aclient.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id)
    
        messages = await aclient.beta.threads.messages.list(thread_id=thread.id)
        latest_mssg = messages.data[0].content[0].text.value
        print(f"generated: {latest_mssg}")
        await send_mssg(TELETOKEN_2, bug_channel, f"тест на работу send_mssg")
        return latest_mssg

    except Exception as e:
        print(f"An error occurred: {e}")
        await send_mssg(TELETOKEN_2, bug_channel, f"exception: {e}")
        return "error"


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


async def run_city(message_body, assistant):
    thread = await aclient.beta.threads.create()
    thread_id = thread.id

    message = await aclient.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body
    )
    new_message = await run_assistant(thread, assistant)
    return new_message


async def generate_response(message_body, usr_id, assistant):
    thread_id = await check_if_thread_exists(usr_id)
    print(message_body, thread_id)

    if thread_id is None:
        print(f"Creating new thread for {usr_id}")
        thread = await aclient.beta.threads.create()
        await store_thread(usr_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread {usr_id}")
        thread = await aclient.beta.threads.retrieve(thread_id)

    message = await aclient.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )
    print(message)

    new_message = await run_assistant(thread, assistant)
    return new_message


async def create_str(data):
    gender = data.get('user_info_gender')
    age = data.get('user_info_age')
    height = data.get('user_info_height')
    weight = data.get('user_info_weight')
    bmr = data.get('bmr')
    tdee = data.get('tdee')
    bmi = data.get('user_info_bmi')
    goal = data.get('user_info_goal')
    print(goal)
    weight_change = data.get('user_info_weight_change')
    pregnancy = data.get('user_info_pregnancy')
    breastfeeding = data.get('user_info_breastfeeding')
    bans = data.get('user_info_meals_ban')
    meal_amount = data.get('user_info_meal_amount')
    extra = data.get('user_info_meals_extra')
    stress = data.get('user_info_stress')
    booze = data.get('user_info_booze')
    water = data.get('user_info_water')
    sleep = data.get('user_info_sleep')
    gym = data.get('user_info_gym_hrs')
    cardio = data.get('user_info_excersise_hrs')
    if goal == "+":
        goalstr = "Набрать"
    elif goal == "-":
        goalstr = "Сбросить"
    elif goal == "=":
        goalstr = "Сохранить вес и здоровье"
    requeststring = f"Я {gender} мне {age} лет, мой рост {height} см, мой вес {weight} кг. Мой bmr = {bmr}, мой tdee = {tdee}, мой bmi = {bmi}, моя цель {goalstr} {weight_change}, я оцениваю свою уровень стресса как: {stress}. Дополнительная важная информация: Статус беременности: {pregnancy}, статус кормления грудью: {breastfeeding}, Мои аллергии: {bans}, Я ем {meal_amount} раз в день, доп информация о приемах еды при наличии: {extra}, Я пью {booze} бокалов алкоголя в неделю, и {water} стаканов воды в день. Сплю в среднем {sleep} часов. Моя физическая нагрузка: {gym} часов силовых упражнений и {cardio} часов кардио"
    return requeststring


async def create_thread_with_extra_info(user_info, usr_id, assistant):
    thread_id = await check_if_yapp_thread_exists(usr_id)
    print( thread_id)

    if thread_id is None:
        print(f"Creating new thread for {usr_id}")
        thread = await aclient.beta.threads.create(
            messages=[

                {
                    "role": "user",
                    "content": user_info
                },
            ]
        )
        await store_yapp_thread(usr_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Thread already exists {usr_id}")
        return "thread already exists"
        thread = await aclient.beta.threads.retrieve(thread_id)
        
    # new_message = await run_assistant(thread, assistant)
    # return new_message
    return f"thread {thread_id} created"


async def yapp_assistant(message_body, usr_id, assistant):
    thread_id = await check_if_yapp_thread_exists(usr_id)
    print(message_body, thread_id)

    if thread_id is None:
        print(f"No thread for {usr_id}")
        return "no thread err"
    else:
        print(f"Retrieving existing thread {usr_id}")
        thread = await aclient.beta.threads.retrieve(thread_id)

    message = await aclient.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )
    print(message)

    new_message = await run_assistant(thread, assistant)
    return new_message

async def rec_assistant(message_body, usr_id, assistant):
    thread_id = await check_if_rec_thread_exists(usr_id)

    if thread_id is None:
        thread = await aclient.beta.threads.create()
        thread_id = thread.id
        await store_rec_thread(usr_id, thread_id)
    else:
        print(f"Retrieving existing thread {usr_id}")
        thread = await aclient.beta.threads.retrieve(thread_id)

    message = await aclient.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )
    print(message)

    new_message = await run_assistant(thread, assistant)
    return new_message

async def no_thread_ass(message_body, assistant):

    thread = await aclient.beta.threads.create()
    message = await aclient.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_body,
    )
    print(message)
    
    new_message = await run_assistant(thread, assistant)
    return new_message
        
