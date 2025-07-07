import requests
import json
import random


# url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
# headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {api_key}"
# }
# data = {
#     "model": "deepseek-ai/DeepSeek-R1",
#     "messages": [
#         {
#             "role": "user",
#             "content": content
#         }
#     ]
# }
# response.json()["choices"][0]["message"]["content"].split('</think>\n')[1]


def generate(history):
    API_KEY = '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'
    API_URL = 'https://openrouter.ai/api/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    # Define the request payload (data)
    data = {
        "model": "deepseek/deepseek-chat:free",
        # "messages": [{"role": "user", "content": "What is the meaning of life?"}]
        'messages': history,
    }

    response = requests.post(API_URL, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]