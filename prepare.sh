ffmpeg -i badapple.mp4 -r 30 frames/output_%04d.png
mkdir -p output
# ffmpeg -i badapple.mp4 -vn -acodec mp3 -ab 40k pd-src/audio.mp3
uv run gen_compressed.py

