from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify
import os
import subprocess
from utils import translate, log_info, log_error, log_warn
from dotenv import load_dotenv
import psutil
import GPUtil
import time
from threading import Thread, Lock
import csv
import pandas as pd
from werkzeug.utils import secure_filename
import urllib.parse

rs_stats = []
lock = Lock()

def collect():
    while True:
        usage = {
            "cpu": psutil.cpu_percent(interval=None),
            "memory": psutil.virtual_memory()._asdict(),
            "gpus": [gpu.__dict__ for gpu in GPUtil.getGPUs()]
        }
        with lock:
            rs_stats.append((time.time(), usage))
            if len(rs_stats) > 1000:
                rs_stats.pop(0)
        time.sleep(0.1)

app = Flask(__name__)
UPLOAD_FOLDER = 'Uploads'
OUTPUT_FOLDER = 'output'
RESOURCE_LOG_FOLDER = os.path.join(OUTPUT_FOLDER, 'resource_logs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(RESOURCE_LOG_FOLDER, exist_ok=True)

def generate_task_id(filename, timestamp):
    time_str = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(timestamp))
    base_filename = secure_filename(filename)
    safe_task_id = f"{base_filename}_{time_str}"
    display_task_id = f"{filename}({time_str})"
    return safe_task_id, display_task_id

def save_rs_stats(task_id, start_time, end_time):
    safe_task_id = task_id[0]
    csv_path = os.path.join(RESOURCE_LOG_FOLDER, f"{safe_task_id}.csv")
    os.makedirs(RESOURCE_LOG_FOLDER, exist_ok=True)
    with lock:
        relevant_stats = [
            (t, data) for t, data in rs_stats
            if start_time <= t <= end_time
        ]
        if not relevant_stats:
            usage = {
                "cpu": psutil.cpu_percent(interval=None),
                "memory": psutil.virtual_memory()._asdict(),
                "gpus": [gpu.__dict__ for gpu in GPUtil.getGPUs()]
            }
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Timestamp', 'CPU_Percent', 'Memory_Total', 'Memory_Used',
            'Memory_Percent', 'GPU_Load', 'GPU_Memory_Used', 'GPU_Memory_Total'
        ])
        for timestamp, data in relevant_stats:
            gpu_load = data['gpus'][0].load * 100 if data['gpus'] else 0
            gpu_mem_used = data['gpus'][0].memoryUsed if data['gpus'] else 0
            gpu_mem_total = data['gpus'][0].memoryTotal if data['gpus'] else 0
            writer.writerow([
                timestamp,
                data['cpu'],
                data['memory']['total'],
                data['memory']['used'],
                data['memory']['percent'],
                gpu_load,
                gpu_mem_used,
                gpu_mem_total
            ])
    log_info(f"Resource usage saved to {csv_path}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('media')
        if not file or not file.filename:
            return render_template('index.html', error="No file uploaded")

        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        start_time = time.time()
        safe_task_id, display_task_id = generate_task_id(filename, start_time)
        log_info(f"Starting task {display_task_id} for file {filename}")

        try:
            subprocess.run(['bash', 'gen.sh', filepath], check=True, timeout=300)
        except subprocess.CalledProcessError as e:
            log_error(f"Transcription failed: {str(e)}")
            return render_template('index.html', error="Failed to generate subtitles")
        except subprocess.TimeoutExpired:
            log_error("Transcription timed out")
            return render_template('index.html', error="Transcription timed out")

        basename = os.path.splitext(filename)[0]
        srt_path = os.path.join(OUTPUT_FOLDER, f"{basename}.srt")
        if not os.path.exists(srt_path):
            log_error(f"Transcription failed: {srt_path} not found")
            return render_template('index.html', error="Transcription failed: SRT file not found")

        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_text = f.read()
        except Exception as e:
            log_error(f"Failed to read SRT file: {str(e)}")
            return render_template('index.html', error="Failed to read subtitles")

        target_langs = request.form.getlist('target_langs')
        translations = {}
        load_dotenv()
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if target_langs and api_key:
            for lang in target_langs:
                log_info(f"Translating to {lang}...")
                try:
                    translated_text = translate(api_key, srt_text, language=lang)
                    log_info(f"Translation to {lang}: {srt_path} completed.")
                    translations[lang] = translated_text
                    zh_path = os.path.join(OUTPUT_FOLDER, f"{basename}.{lang}.srt")
                    with open(zh_path, 'w', encoding='utf-8') as f:
                        f.write(translated_text)
                except Exception as e:
                    log_error(f"Translation to {lang} failed: {str(e)}")
                    translations[lang] = f"Translation failed: {str(e)}"

        end_time = time.time()
        save_rs_stats((safe_task_id, display_task_id), start_time, end_time)
        log_info(f"Task {display_task_id} completed")

        return render_template('index.html',
                            filename=filename,
                            srt_content=srt_text,
                            translations=translations)
    return render_template('index.html')

@app.route('/play/<filename>', methods=['POST'])
def play_with_mpv(filename):
    basename = os.path.splitext(filename)[0]
    video_path = os.path.join(UPLOAD_FOLDER, filename)
    subtitle_files = [os.path.join(OUTPUT_FOLDER, f"{basename}.srt")]
    lang_codes = ['zh-cn', 'zh-hk', 'ja', 'ko']
    for lang in lang_codes:
        srt_path = os.path.join(OUTPUT_FOLDER, f"{basename}.{lang}.srt")
        if os.path.exists(srt_path):
            subtitle_files.append(srt_path)

    cmd = ["mpv", video_path, "--fs"]
    for srt_file in subtitle_files:
        cmd += [f"--sub-file={srt_file}"]
    log_info(f"Running command: {' '.join(cmd)}")

    try:
        subprocess.Popen(cmd)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/status')
def status():
    with lock:
        return jsonify(rs_stats[-1][1] if rs_stats else {})

@app.route('/task_list')
def task_list():
    tasks = [f[:-4] for f in os.listdir(RESOURCE_LOG_FOLDER) if f.endswith('.csv')]
    display_tasks = []
    for task in tasks:
        parts = task.rsplit('_', 1)
        if len(parts) == 2:
            display_task = f"{parts[0]}({parts[1]})"
            display_tasks.append(display_task)
        else:
            display_tasks.append(task)
    return jsonify({"tasks": display_tasks})

@app.route('/resource_data/<path:task_id>')
def resource_data(task_id):
    task_id = urllib.parse.unquote(task_id)
    safe_task_id = task_id.replace('(', '_').replace(')', '')
    csv_path = os.path.join(RESOURCE_LOG_FOLDER, f"{safe_task_id}.csv")
    if not os.path.exists(csv_path):
        return jsonify({"error": "Task not found"}), 404
    try:
        df = pd.read_csv(csv_path)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        log_error(f"Failed to read CSV {csv_path}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/monitor')
def monitor():
    return render_template('monitor.html')

if __name__ == '__main__':
    Thread(target=collect, daemon=True).start()
    app.run(debug=True)