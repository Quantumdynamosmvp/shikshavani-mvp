import os
from typing import List
from flask import Flask, request, jsonify
from moviepy.editor import concatenate_videoclips, VideoFileClip
from google.cloud import storage
import logging

# Configure logging
logging.basicConfig(
    format='[generate_video] %(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = Flask(__name__)

def concatenate_videos(video_list: List[str], output_path: str) -> bool:
    if not video_list:
        logging.error("No video files provided for concatenation")
        return False
        
    if not all(isinstance(v, str) for v in video_list):
        logging.error("Invalid video path format in input list")
        return False

    clips = []
    try:
        for video_path in video_list:
            if not os.path.exists(video_path):
                logging.warning(f"Video file not found: {video_path}")
                continue

            try:
                clip = VideoFileClip(video_path)
                if clip.duration > 0:
                    clips.append(clip)
                else:
                    clip.close()
                    logging.warning(f"Skipping empty clip: {video_path}")
            except Exception as e:
                logging.error(f"Failed to load clip {video_path}: {e}")
                continue

        if not clips:
            logging.error("No valid video clips found for concatenation")
            return False

        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=6,
            preset='fast',
            logger=None,
            ffmpeg_params=[
                '-movflags', '+faststart',
                '-crf', '23'
            ]
        )
        logging.info(f"Successfully created concatenated video: {output_path}")
        return True

    except Exception as e:
        logging.error(f"Video concatenation failed: {e}")
        return False
        
    finally:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        if 'final_clip' in locals():
            try:
                final_clip.close()
            except Exception:
                pass

def upload_to_gcs(local_path: str, bucket_name: str, destination_blob_name: str) -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_path)

    # Return public URL (no ACL, assuming uniform bucket-level access is ON)
    public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
    return public_url

@app.route("/final_video", methods=["POST"])
def final_video_endpoint():
    try:
        data = request.json
        video_list = data.get("video_list", [])
        if not video_list:
            return jsonify({"status": "error", "message": "No video list provided"}), 400

        os.makedirs("final_videos", exist_ok=True)
        output_path = "final_videos/complete_video.mp4"
        success = concatenate_videos(video_list, output_path)

        if not success:
            return jsonify({"status": "error", "message": "Video concatenation failed"}), 500

        public_url = upload_to_gcs(
            local_path=output_path,
            bucket_name="vidpro-bucket1",
            destination_blob_name="final_video/complete_video.mp4"
        )

        return jsonify({
            "status": "success",
            "url": public_url
        }), 200

    except Exception as e:
        logging.error(f"Unexpected error in /final_video: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Local test
    test_videos = [
        "final_videos/section_0.mp4",
        "final_videos/section_1.mp4"
    ]
    existing_videos = [v for v in test_videos if os.path.exists(v)]
    
    if concatenate_videos(existing_videos, "final_videos/complete_video.mp4"):
        print("Test concatenation successful")
    else:
        print("Test concatenation failed")
