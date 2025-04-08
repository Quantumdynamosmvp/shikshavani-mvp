from flask import Flask, request, jsonify
import os
from text_animation import create_text_animation_video, overlay_text_on_video
from generate_video import concatenate_section_videos
from google.cloud import storage
import uuid
import shutil

app = Flask(__name__)

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

BUCKET_NAME = "vidpro-bucket1"

def upload_to_gcs(local_path, gcs_filename):
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_filename)
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url

@app.route("/generate_section", methods=["POST"])
def generate_section():
    try:
        data = request.json
        section_id = data["section_id"]
        text = data["text"]
        audio_path = data["audio_path"]
        background_video_path = data["background_path"]

        text_anim_path = os.path.join(TEMP_DIR, f"text_anim_{section_id}.mp4")
        final_section_path = os.path.join(TEMP_DIR, f"section_{section_id}.mp4")

        from moviepy.editor import AudioFileClip
        duration = AudioFileClip(audio_path).duration

        create_text_animation_video(text, (854, 720), duration, text_anim_path)
        overlay_text_on_video(
            None, text, final_section_path, background_video_path, audio_path, text_anim_path
        )

        return jsonify({"message": "Section video generated", "section_path": final_section_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/final_video", methods=["POST"])
def final_video():
    try:
        data = request.json
        section_paths = data["section_paths"]  # list of file paths
        final_video_path = os.path.join(TEMP_DIR, "complete_video.mp4")

        concatenate_section_videos(section_paths, final_video_path)

        # Upload to GCS
        gcs_filename = f"final_videos/complete_video_{uuid.uuid4()}.mp4"
        public_url = upload_to_gcs(final_video_path, gcs_filename)

        # Clean up
        shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)

        return jsonify({"final_video_url": public_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health():
    return "Text animation Cloud Run service is up!", 200
