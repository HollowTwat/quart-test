from quart import Quart, request, jsonify
# from bot2 import OPENAI_API_KEY, handle_assistant_response, encode_image, use_vision64
import openai
import requests
import base64


client = openai.OpenAI(api_key=OPENAI_API_KEY)

openai.api_key = OPENAI_API_KEY

app = Quart(__name__)


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

5


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
