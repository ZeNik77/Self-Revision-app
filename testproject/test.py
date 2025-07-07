import requests

# Replace with your OpenRouter API key
API_KEY = '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'
API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Define the headers for the API request
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# Define the request payload (data)
data = {
    "model": "deepseek/deepseek-chat:free",
    "messages": [{"role": "user", "content": "What is the meaning of life?"}]
}

# Send the POST request to the DeepSeek API
response = requests.post(API_URL, json=data, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    print("API Response:", response.json())
else:
    print("Failed to fetch data from API. Status Code:", response.status_code)
