from quart import Quart, request, jsonify
from bot2 import OPENAI_API_KEY, handle_assistant_response, encode_image, use_vision64
import openai
import requests

client = openai.OpenAI(api_key=OPENAI_API_KEY)

openai.api_key = OPENAI_API_KEY

app = Quart(__name__)


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


@app.route("/")
async def home():
    return "Home"


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

    return jsonify(transcription, assistant_response), 201


@app.route("/img", methods=["POST"])
async def process_image():
    data = await request.get_json()

    url = data.get('url')
    vision = await use_vision64_from_url(url)
    # vision1 = jsonify(vision).content

    return jsonify(vision), 201


if __name__ == "__main__":
    # app.run(port=8080, debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
