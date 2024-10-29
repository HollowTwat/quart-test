from quart import Quart, request, jsonify, render_template
from cal_pretty import prettify_and_count
from functions import *
import json
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
import random
from datetime import datetime, timedelta
from sale_stickers import STICKERLIST, STICKERLIST_2

sticker_id = "CAACAgIAAxkBAAIHp2aLyyiL4UY-FICRxHkMxTBvi9jkAAIXUAAC8R5hSFFY0DLWfFtzNQQ"
# "CAACAgIAAxkBAAIE62aF2oFJ5Ltu03_xMZWrC40hoAABzAACGUEAAqIlcUhMnKnBWnZogDUE" CAACAgIAAxkBAAIINGaMcaRe9fVOeaZTFZyWWWM6CrnHAAIBTQACA09oSDqGGMuDHw4tNQQ
active_threads = {}
REQUEST_TIMEOUT = 5

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VISION_ASSISTANT_ID = os.getenv('VISION_ASSISTANT_ID')
CITY_ASSISTANT_ID = os.getenv('CITY_ASSISTANT_ID')
ASSISTANT2_ID = os.getenv('ASSISTANT2_ID')
YAPP_SESH_ASSISTANT_ID = os.getenv('YAPP_SESH_ASSISTANT_ID')
RATE_DAY_ASS_ID = os.getenv('RATE_DAY_ASS_ID')
RATE_MID_ASS_ID = os.getenv('RATE_MID_ASS_ID')
RATE_SMOL_ASS_ID = os.getenv('RATE_SMOL_ASS_ID')
RATE_WEEK_ASS_ID = os.getenv('RATE_WEEK_ASS_ID')
RATE_TWONE_ASS_ID = os.getenv('RATE_TWONE_ASS_ID')
ETIK_ASS_ID = os.getenv('ETIK_ASS_ID')
RECIPE_ASS_ID = os.getenv('RECIPE_ASS_ID')
RATE_TRIAL_ASS_ID = os.getenv('RATE_TRIAL_ASS_ID')
VISION_ASS_ID_2 = os.getenv("VISION_ASS_ID_2")
client = openai.OpenAI(api_key=OPENAI_API_KEY)
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai.api_key = OPENAI_API_KEY

PORT = os.getenv('PORT')           # get the port generated by railway
TELETOKEN = os.getenv('TELEBOT')
TELETOKEN_2 = os.getenv('TELEBOT_2')
file_url = "https://github.com/HollowTwat/quart-test/blob/main/hmm.gif?raw=true"

# app = Quart(__name__)
app = Quart(__name__, static_url_path='/static')
# required to get a visitors IP through railway
app.config["SESSION_REVERSE_PROXY"] = True
Compress(app)


# @app.listen(PORT, '::', ()
#     print(f"Server listening on [::]{PORT}")

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


def get_correct_ass(size):
    ass_mapping = {
        'trial': f"{RATE_TRIAL_ASS_ID}",
        'big': f"{RATE_DAY_ASS_ID}",
        'mid': f"{RATE_MID_ASS_ID}",
        'smol': f"{RATE_SMOL_ASS_ID}",
        'week': f"{RATE_WEEK_ASS_ID}",
        'twone': f"{RATE_TWONE_ASS_ID}"
    }

    return ass_mapping.get(size)


@app.route("/")
async def index() -> str:
    return await render_template("index.html")

@app.route("/stickers", methods=["POST"])
async def stickers():
    data = await request.get_json()
    id = data.get('id')
    for sticker_id in STICKERLIST:
        await send_sticker(TELETOKEN, id, sticker_id)
    return "done", 200
    


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
    id = data.get('id')
    await remove_thread(id)
    return "removed", 201

@app.route("/remove_rec", methods=["POST"])
async def thread_rec_remove():
    data = await request.get_json()
    id = data.get('id')
    await remove_rec_thread(id)
    return "removed", 201


@app.route("/city", methods=["POST"])
async def city_quip():
    data = await request.get_json()
    
    goal = data.get('goal')
    city = data.get('city')
    message_body = f"цель {goal} город {city}"
    print(message_body)
    response = await run_city(message_body, CITY_ASSISTANT_ID)
    return response, 201


@app.route("/oga", methods=["POST"])
async def transcribe():
    data = await request.get_json()

    url = data.get('url')
    id = data.get('id')
    transcription = await transcribe_audio_from_url(url)
    await send_mssg(TELETOKEN, id, f"Транскрипция: {transcription}")
    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    print(result)
    message = result.get("result")
    mssg_id = message.get("message_id")
    outputtype = data.get('outputtype')
    if outputtype == "1":
        assistant_response = await generate_response(transcription, id, VISION_ASSISTANT_ID)
        counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    else:
        assistant_response = await generate_response(transcription, id, VISION_ASS_ID_2)
        counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    await delete_message(TELETOKEN, id, mssg_id)
    if isinstance(counted, dict) and counted.get("error") == "error":
        Iserror = True
    else:
        Iserror = False
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": counted if isinstance(counted, dict) else json.loads(counted)    
    })

    return Final, 201


@app.route("/txt", methods=["POST"])
async def process_txt():
    print('txt triggered')
    data = await request.get_json()
    txt = data.get('txt')
    id = data.get('id')
    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    message = result.get("result")
    mssg_id = message.get("message_id")
    outputtype = data.get('outputtype')

    if outputtype == "1":
        assistant_response = await generate_response(txt, id, VISION_ASSISTANT_ID)
        counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    else:
        assistant_response = await generate_response(txt, id, VISION_ASS_ID_2)
        counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    # vision1 = jsonify(vision).content
    await delete_message(TELETOKEN, id, mssg_id)
    if isinstance(counted, dict) and counted.get("error") == "error":
        Iserror = True
    else:
        Iserror = False
    Final = jsonify(
        {
            "IsError": str(Iserror),
            "Answer": counted if isinstance(counted, dict) else json.loads(counted)    
    })
    return Final, 201


@app.route("/imggg", methods=["POST"])
async def image_proc():
    print('imGGG triggered')

    data = await request.get_json()
    print(request)
    print(data)
    url = data.get('url')
    id = data.get('id')

    now = datetime.now()
    expiration_time = active_threads.get(id)

    if expiration_time and expiration_time > now:
        return jsonify({
        "IsError": "True",
        "Answer": {
            "error": "DoubleTap"
        }
    }), 429
    
    active_threads[id] = now + timedelta(seconds=REQUEST_TIMEOUT)
    try:

        print(data, url, id, TELETOKEN)
        result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
        message = result.get("result")
        mssg_id = message.get("message_id")
        outputtype = data.get('outputtype')

        if outputtype == "1":
            vision = await process_url(url, id, VISION_ASSISTANT_ID)
            counted = await prettify_and_count(vision, detailed_format=(outputtype == "0"))
        else:
            vision = await process_url(url, id, VISION_ASS_ID_2)
            counted = await prettify_and_count(vision, detailed_format=(outputtype == "0"))
        await delete_message(TELETOKEN, id, mssg_id)
        if isinstance(counted, dict) and counted.get("error") == "error":
            Iserror = True
        else:
            Iserror = False
        Final = json.dumps(
            {
                "IsError": str(Iserror),
                "Answer": counted if isinstance(counted, dict) else json.loads(counted)    
        })
        return Final, 201
    
    except Exception as e:
        # Remove the lock if an error occurs
        active_threads.pop(id, None)
        return jsonify({
            "IsError": "True",
            "error": f"An error occurred: {str(e)}"
        }), 500


@app.route("/edit_oga", methods=["POST"])
async def edit_audio():
    print('edit_oga triggered')

    data = await request.get_json()
    url = data.get('url')
    id = data.get('id')
    old = data.get('extra')
    outputtype = data.get('outputtype')

    transcription = await transcribe_audio_from_url(url)
    await send_mssg(TELETOKEN, id, f"Транскрипция: {transcription}")
    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    message = result.get("result")
    mssg_id = message.get("message_id")
    if outputtype == "1":
        assistant_response = await generate_response(f"Старый прием пищи: {old} отредактируй его вот так: {transcription}", id, VISION_ASSISTANT_ID)
        counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    else:
        assistant_response = await generate_response(f"Старый прием пищи: {old} отредактируй его вот так: {transcription}", id, VISION_ASS_ID_2)
        counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    await delete_message(TELETOKEN, id, mssg_id)
    if isinstance(counted, dict) and counted.get("error") == "error":
        Iserror = True
    else:
        Iserror = False
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": counted if isinstance(counted, dict) else json.loads(counted)    
    })
    return Final, 201


@app.route("/edit_txt", methods=["POST"])
async def edit_txt():
    print('edit_txt triggered')

    data = await request.get_json()
    txt = data.get('txt')
    id = data.get('id')
    old = data.get('extra')
    outputtype = data.get('outputtype')

    print(txt, id, old)
    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    message = result.get("result")
    mssg_id = message.get("message_id")
    if outputtype == "1":
        assistant_response = await generate_response(f"Старый прием пищи: {old} отредактируй его вот так: {txt}", id, VISION_ASSISTANT_ID)
        counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    else: 
        assistant_response = await generate_response(f"Старый прием пищи: {old} отредактируй его вот так: {txt}", id, VISION_ASS_ID_2)
        counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    await delete_message(TELETOKEN, id, mssg_id)
    if isinstance(counted, dict) and counted.get("error") == "error":
        Iserror = True
    else:
        Iserror = False
    
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": counted if isinstance(counted, dict) else json.loads(counted)    
    })
    return Final, 201


@app.route("/day1/yapp_create", methods=["POST"])
async def yapp_thread_input():
    print('day1_yapp_create triggered')
    data = await request.get_json()
    print(data)
    id = data.get('id')
    user_info_str = await create_str(data)
    info_to_send_to_gpt = f"Инфа: {user_info_str}"  # republish
    thread_id = await check_if_yapp_thread_exists(id)
    if thread_id is None:
        response = await create_thread_with_extra_info(user_info_str, id, YAPP_SESH_ASSISTANT_ID)
    else:
        response = "thread allready exists"
    return response, 201


@app.route("/yapp_remove", methods=["POST"])
async def yapp_thread_remove():
    data = await request.get_json()
    id = data.get('id')
    await remove_yapp_thread(id)
    return "removed", 201

@app.route("/day1/yapp", methods=["POST"])
async def yapp():
    print('day1_yapp triggered')
    data = await request.get_json()
    print(data)
    id = data.get('id')
    question = data.get('txt')

    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    message = result.get("result")
    mssg_id = message.get("message_id")

    response = await yapp_assistant(question, id, YAPP_SESH_ASSISTANT_ID)
    if response != "error":
        Iserror = False
        Jsoned = {
                "extra": str(response)
            }
    elif response == "error":
        Iserror = True
        Jsoned = {
                "error": str(response)
            }
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": Jsoned    
    })
    await delete_message(TELETOKEN, id, mssg_id)
    return Final, 201


@app.route("/day1/yapp_oga", methods=["POST"])
async def yapp_oga():
    print('day1_oga_yapp')
    data = await request.get_json()
    id = data.get('id')
    question = data.get('txt')
    transcription = await transcribe_audio_from_url(question)

    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    message = result.get("result")
    mssg_id = message.get("message_id")

    response = await yapp_assistant(transcription, id, YAPP_SESH_ASSISTANT_ID)
    if response != "error":
        Iserror = False
        Jsoned = {
                "extra": str(response)
            }
    elif response == "error":
        Iserror = True
        Jsoned = {
                "error": str(response)
            }
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": Jsoned    
    })
    await delete_message(TELETOKEN, id, mssg_id)
    return Final, 201


@app.route("/rate_day", methods=["POST"])
async def rate_day():
    print('rate_day')
    print(request)
    data = await request.get_json()
    print(data)
    id = data.get('id')
    question = data.get('txt')

    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    message = result.get("result")
    mssg_id = message.get("message_id")

    assistant_response = await no_thread_ass(question, RATE_DAY_ASS_ID)
    if assistant_response != "error":
        Iserror = False
        Jsoned = {
                "extra": str(assistant_response)
            }
    elif assistant_response == "error":
        Iserror = True
        Jsoned = {
                "error": str(assistant_response)
            }
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": Jsoned    
    })
    await delete_message(TELETOKEN, id, mssg_id)
    return Final, 201


@app.route("/rate_any", methods=["POST"])
async def rate_any():
    print('rate_any')
    print(request)
    data = await request.get_json()
    print(data)
    size = data.get('assistanttype')
    id = data.get('id')
    question = data.get('txt')
    ass = get_correct_ass(size)

    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    message = result.get("result")
    mssg_id = message.get("message_id")

    assistant_response = await no_thread_ass(question, ass)
    if assistant_response != "error":
        Iserror = False
        assistant_response_clean = await remove_reference(assistant_response)
        Jsoned = {
                "extra": str(assistant_response_clean)
            }
    elif assistant_response == "error":
        Iserror = True
        Jsoned = {
                "error": str(assistant_response)
            }
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": Jsoned    
    })
    await delete_message(TELETOKEN, id, mssg_id)
    return Final, 201

@app.route("/etik", methods=["POST"])
async def etik_proc():
    print('etik triggered')

    data = await request.get_json()
    print(data)
    url = data.get('url')
    id = data.get('id')
    allergies = data.get('extra')
    print(data, url, id, TELETOKEN)
    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    message = result.get("result")
    mssg_id = message.get("message_id")
    outputtype = data.get('outputtype')
    
    vision = await process_url_etik(url, allergies, id, ETIK_ASS_ID)
    if vision != "error":
        Iserror = False
        Jsoned = {
                "extra": str(vision)
            }
    elif vision == "error":
        Iserror = True
        Jsoned = {
                "error": str(vision)
            }
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": Jsoned  
    })
    await delete_message(TELETOKEN, id, mssg_id)
    print(Final)
    return Final, 201

@app.route("/recipe_oga", methods=["POST"])
async def proc_recipe_oga():
    data = await request.get_json()

    url = data.get('url')
    id = data.get('id')
    extra = data.get('extra')
    transcription = await transcribe_audio_from_url(url)
    await send_mssg(TELETOKEN, id, f"Транскрипция: {transcription}")
    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    print(result)
    message = result.get("result")
    mssg_id = message.get("message_id")

    question_with_extra = f"question:{transcription}, extra:{extra}"
    assistant_response = await rec_assistant(question_with_extra, id, RECIPE_ASS_ID)
    await delete_message(TELETOKEN, id, mssg_id)
    if assistant_response != "error":
        Iserror = False
        Jsoned = {
                "extra": str(assistant_response)
            }
    elif assistant_response == "error":
        Iserror = True
        Jsoned = {
                "error": str(assistant_response)
            }
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": Jsoned    
    })
    return Final, 201

@app.route("/recipe_txt", methods=["POST"])
async def proc_recipe_txt():
    data = await request.get_json()

    txt = data.get('txt')
    id = data.get('id')
    extra = data.get('extra')
    
    result = await send_sticker(TELETOKEN, id, random.choice(STICKERLIST))
    print(result)
    message = result.get("result")
    mssg_id = message.get("message_id")

    question_with_extra = f"question:{txt}, extra:{extra}"
    assistant_response = await rec_assistant(question_with_extra, id, RECIPE_ASS_ID)
    await delete_message(TELETOKEN, id, mssg_id)
    if assistant_response != "error":
        Iserror = False
        Jsoned = {
                "extra": str(assistant_response)
            }
    elif assistant_response == "error":
        Iserror = True
        Jsoned = {
                "error": str(assistant_response)
            }
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": Jsoned    
    })
    return Final, 201

@app.route("/oga_2", methods=["POST"])
async def transcribe_2():
    data = await request.get_json()

    url = data.get('url')
    id = data.get('id')
    transcription = await transcribe_audio_from_url(url)
    await send_mssg(TELETOKEN_2, id, f"Транскрипция: {transcription}")
    result = await send_sticker(TELETOKEN_2, id, random.choice(STICKERLIST_2))
    print(result)
    message = result.get("result")
    mssg_id = message.get("message_id")
    outputtype = data.get('outputtype')

    assistant_response = await generate_response(transcription, id, VISION_ASSISTANT_ID)
    counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    await delete_message(TELETOKEN_2, id, mssg_id)
    if isinstance(counted, dict) and counted.get("error") == "error":
        Iserror = True
    else:
        Iserror = False
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": counted if isinstance(counted, dict) else json.loads(counted)    
    })
    return Final, 201


@app.route("/txt_2", methods=["POST"])
async def process_txt_2():
    print('txt triggered')
    data = await request.get_json()
    txt = data.get('txt')
    id = data.get('id')
    result = await send_sticker(TELETOKEN_2, id, random.choice(STICKERLIST_2))
    message = result.get("result")
    mssg_id = message.get("message_id")
    outputtype = data.get('outputtype')

    assistant_response = await generate_response(txt, id, VISION_ASSISTANT_ID)
    counted = await prettify_and_count(assistant_response, detailed_format=(outputtype == "0"))
    # vision1 = jsonify(vision).content
    await delete_message(TELETOKEN_2, id, mssg_id)
    if isinstance(counted, dict) and counted.get("error") == "error":
        Iserror = True
    else:
        Iserror = False
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": counted if isinstance(counted, dict) else json.loads(counted)    
    })
    return Final, 201


@app.route("/imggg_2", methods=["POST"])
async def image_proc_2():
    print('imGGG triggered')

    data = await request.get_json()
    print(request)
    print(data)
    url = data.get('url')
    id = data.get('id')
    print(data, url, id, TELETOKEN_2)
    result = await send_sticker(TELETOKEN_2, id, random.choice(STICKERLIST_2))
    message = result.get("result")
    mssg_id = message.get("message_id")
    outputtype = data.get('outputtype')

    vision = await process_url(url, id, VISION_ASSISTANT_ID)
    counted = await prettify_and_count(vision, detailed_format=(outputtype == "0"))
    await delete_message(TELETOKEN_2, id, mssg_id)
    if isinstance(counted, dict) and counted.get("error") == "error":
        Iserror = True
    else:
        Iserror = False
    Final = json.dumps(
        {
            "IsError": str(Iserror),
            "Answer": counted if isinstance(counted, dict) else json.loads(counted)    
    })
    return Final, 201

@app.route("/test", methods=["POST"])
async def test():
    data = await request.get_json()
    print(data)
    return data, 201

if __name__ == "__main__":
    # app.run(port=8080, debug=True)
    app.run(host='::', port=PORT, debug=True)
