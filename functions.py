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
