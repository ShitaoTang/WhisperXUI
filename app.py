from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify
import os
import subprocess
from utils import translate, log_info, log_error, log_warn
from dotenv import load_dotenv

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['media']
        if file:
            filename = file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            subprocess.run(['bash', 'gen.sh', filepath], check=True)

            basename = os.path.splitext(filename)[0]
            srt_path = os.path.join(OUTPUT_FOLDER, f"{basename}.srt")
            if not os.path.exists(srt_path):
                return f"❌ Transcription failed: {srt_path} not found", 500

            with open(srt_path, 'r') as f:
                srt_text = f.read()

            target_langs = request.form.getlist('target_langs')

            translations = {}
            load_dotenv()
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if target_langs and api_key:
                for lang in target_langs:
                    log_info(f"Translating to {lang}...")
                    translated_text = translate(api_key, srt_text, language=lang)
                    log_info(f"Translation to {lang}: {srt_path} completed.")
                    translations[lang] = translated_text

                    zh_path = os.path.join(OUTPUT_FOLDER, f"{basename}.{lang}.srt")
                    with open(zh_path, 'w', encoding='utf-8') as f:
                        f.write(translated_text)
            else:
                log_info("Skipping translation or missing API key.")

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

if __name__ == '__main__':
    app.run(debug=True)
