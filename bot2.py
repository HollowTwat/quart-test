import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ContentType, Voice
from aiogram.filters import Command
from aiogram.dispatcher.event.bases import SkipHandler
import openai
from openai import OpenAI
# Assuming this is a custom module you have for handling OpenAI interactions
import openai_utils
import aiofiles
import aiohttp
import base64
import requests


client = OpenAI(api_key=OPENAI_API_KEY)

openai.api_key = OPENAI_API_KEY

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


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

    print(response.json())
    return str(response.json())


async def use_vision(file_path):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What’s in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    print(response.choices[0])
    return response.choices[0]


async def transcribe_audio(file_path):
    async with aiofiles.open(file_path, 'rb') as audio_file:
        audio_data = await audio_file.read()
    response = openai.audio.transcriptions.create(
        model="whisper-1",
        file=open(file_path, "rb")
    )
    return response.text


async def transcribe_audio_from_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                audio_data = await response.read()
                with open('temp_audio.ogg', 'wb') as f:
                    f.write(audio_data)
                return await transcribe_audio('temp_audio.ogg')
            else:
                raise Exception(
                    f"Failed to fetch audio from URL: {response.status}")


async def use_vision64_from_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                with open('temp_img.jpg', 'wb') as f:
                    f.write(image_data)
                return await use_vision64('temp_img.jpg')
            else:
                raise Exception(
                    f"Failed to fetch video from URL: {response.status}")


async def handle_assistant_response(prompt):
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()


async def send_image_to_gpt4_vision(image_path):
    with open(image_path, 'rb') as image_file:
        response = client.embeddings.create(
            assistant_id=GPT4_VISION_ASSISTANT_ID,
            file=image_file
            # model="dall-e"  # Replace with the correct model name if needed
        )
    return response['choices'][0]['text']


async def handle_image_response(image_path):
    # This is a placeholder for the image handling logic
    # Implement your image processing logic here
    return "Image processed successfully."


@dp.message(Command(commands=["start"]))
async def handle_start_command(message: Message):
    await message.answer("Hello! Send me a voice message to transcribe or a photo to process.")


@dp.message(lambda message: message.content_type == ContentType.VOICE)
async def handle_voice_message(message: Message):
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    await bot.download_file(file_path, 'voice_message.ogg')

    transcription = await transcribe_audio('voice_message.ogg')
    assistant_response = await handle_assistant_response(transcription)

    await message.answer(f"Transcription: {transcription}\nAssistant: {assistant_response}")


@dp.message(lambda message: message.content_type == ContentType.PHOTO)
async def handle_photo(message: Message):
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    await bot.download_file(file_path, 'image.jpg')

    vision_response = await use_vision64('image.jpg')
    # gpt4_vision_response = await send_image_to_gpt4_vision('image.jpg')

    await message.answer(f"Assistant: {vision_response}")


# @dp.message(lambda message: message.text in [])
@dp.message(lambda message: message.content_type == ContentType.TEXT)
async def handle_ogg_url(message: Message):
    url = message.text.strip()
    if url.endswith(".ogg") or url.endswith(".oga"):
        try:
            transcription = await transcribe_audio_from_url(url)
            assistant_response = await handle_assistant_response(transcription)
            await message.answer(f"Transcription: {transcription}\nAssistant: {assistant_response}")
        except Exception as e:
            await message.answer(f"Failed to transcribe audio from URL: {str(e)}")
    elif url.endswith(".png") or url.endswith(".jpg") or url.endswith(".jpeg"):
        try:
            img_resp = await use_vision64_from_url(url)
            await message.answer(img_resp)
        except Exception as e:
            await message.answer(f"Failed to process URL: {str(e)}")
    else:
        await message.answer("The URL does not point to a valid file.")


if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)
