import requests
import json
import random

def generateTest(topic_name, topic_description):
    jsonString = '[{"question": "Question text", "answer": ["Correct answer", "Wrong answer 1", "Wrong answer 2"]}, ...]'
    content = "Generate a 5 single-choice questions test on the topic \""+topic_name+"\" with the content \""+topic_description+"\". Format your answer strictly as a valid JSON array in a single line, like this: "+jsonString+"Do not add any commentary, preamble, or explanation. Your response must be a single JSON string without any line breaks or \ escape characters. The first answer in each array must be the correct one."
    url = "https://api.intelligence.io.solutions/api/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    
    # return json.loads(response.json()["choices"][0]["message"]["content"])
    test = json.loads(response.json()["choices"][0]["message"]["content"].split('</think>\n')[1])
    correct = []
    for i in range(len(test)):
        q = test[i]
        question = q['question']
        answer = q['answer']
        correct.append(answer[0])
        random.shuffle(answer)
        test[i] = {'number': i+1, 'question': question, 'answer': answer}
    return (test, correct)

api_key = 'io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjliMTVlODBmLWY3ODUtNDEzYy1hZjhiLTE5NDU4ODI5MTY4NSIsImV4cCI6NDkwNDUzOTE2N30.Xo4MbPTYxcjEq1TMwNQ_YTrGalMEn7U4oDOiadVsSnJbZiK_pRvh4pBU6UH8qr9uaVOKc1ryW6Yc--7ih0Ec6Q'
if __name__ == '__main__':
    from pprint import pprint
    # pprint(generateTest('Градиент', 'Градиент — это вектор, указывающий направление наибольшего возрастания функции. Для функции нескольких переменных f(x, y, z...) градиент ∇f = (∂f/∂x, ∂f/∂y, ∂f/∂z, ...) состоит из её частных производных. Он показывает, как и куда функция возрастает быстрее всего. Если градиент равен нулю, это может быть точка экстремума.', 0, 0, 0))
