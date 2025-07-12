import requests

def translate(api_key, text, language='zh-cn'):
    headers = {"Authorization": f"Bearer {api_key}"}
    prompt = f"Translate the following text into {language} without any additional explanations."

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
    }

    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        json=payload,
        headers=headers
    )
    result = response.json()

    if 'choices' in result and result['choices']:
        return result['choices'][0]['message']['content']
    else:
        raise RuntimeError(f"Translation failed: {result}")
    
def log_info(msg): print(f"\033[32m[INFO]\033[0m {msg}")
def log_error(msg): print(f"\033[31m[ERROR]\033[0m {msg}")
def log_warn(msg): print(f"\033[33m[WARN]\033[0m {msg}")