import requests
from pynvml import (
    nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetCount,
    nvmlDeviceGetUtilizationRates, nvmlDeviceGetMemoryInfo
)

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

nvml_init_failed = False

def get_gpu_info():
    global nvml_init_failed
    try:
        nvmlInit()
        gpus = []
        for i in range(nvmlDeviceGetCount()):
            handle = nvmlDeviceGetHandleByIndex(i)
            util = nvmlDeviceGetUtilizationRates(handle)
            mem = nvmlDeviceGetMemoryInfo(handle)
            gpus.append({
                "id": i,
                "load": util.gpu / 100.0,
                "memoryUsed": mem.used // (1024 * 1024),
                "memoryTotal": mem.total // (1024 * 1024)
            })
        return gpus
    except Exception as e:
        if not nvml_init_failed:
            log_warn(f"Failed to fetch GPU info: {str(e)}")
            nvml_init_failed = True
        return []