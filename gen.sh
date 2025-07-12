#!/bin/bash
set -e

WHISPERCPP_PATH="$PWD/whisper.cpp"
INPUT="$1"
MODEL="$WHISPERCPP_PATH/models/ggml-base.en.bin"
TMP_WAV="tmp_audio.wav"
BASENAME=$(basename "$INPUT")
BASENAME_NOEXT="${BASENAME%.*}"
OUTPUT_DIR="output"

GREEN=$'\033[32m'
RED=$'\033[31m'
NC=$'\033[0m'

if [ -z "$INPUT" ]; then
  echo "${RED}[ERROR]${NC} Usage: $0 <audio_or_video_file>"
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "${RED}[ERROR]${NC} File not found: $INPUT"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "${GREEN}[INFO]${NC} Extracting audio from '$INPUT'..."
ffmpeg -y -i "$INPUT" -ac 1 -ar 16000 -vn "$TMP_WAV" > /dev/null 2>&1

export LD_LIBRARY_PATH="$WHISPERCPP_PATH/build/src:$WHISPERCPP_PATH/build/ggml/src:$LD_LIBRARY_PATH"

echo "${GREEN}[INFO]${NC} Running Whisper..."
"$WHISPERCPP_PATH/build/bin/whisper-cli" -m "$MODEL" -f "$TMP_WAV" -l en -otxt -osrt -of "$OUTPUT_DIR/$BASENAME_NOEXT"

echo "${GREEN}[INFO]${NC} Done. Output files:"
ls "$OUTPUT_DIR/$BASENAME_NOEXT".*

# # embed srt into source video and generate a new video (only if input is a video)
# case "$INPUT" in
#   *.mp4|*.mov|*.mkv)
#     echo "🎞️  Muxing subtitles into video..."
#     ffmpeg -y -i "$INPUT" -vf subtitles="$OUTPUT_DIR/$BASENAME_NOEXT.srt" \
#            -c:a copy "$OUTPUT_DIR/${BASENAME_NOEXT}_subtitled.mp4" > /dev/null 2>&1
#     echo "🎬 Subtitled video: $OUTPUT_DIR/${BASENAME_NOEXT}_subtitled.mp4"
#     ;;
#   *)
#     ;;
# esac

rm -f "$TMP_WAV"
