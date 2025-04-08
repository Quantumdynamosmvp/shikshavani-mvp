import os
from typing import List
from moviepy.editor import concatenate_videoclips, VideoFileClip
import logging

# Configure logging
logging.basicConfig(
    format='[generate_video] %(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def concatenate_videos(video_list: List[str], output_path: str) -> bool:
    """
    Optimized video concatenation function with enhanced error handling and resource management.
    
    Args:
        video_list: List of paths to video files to concatenate
        output_path: Path for the final output video file
        
    Returns:
        bool: True if concatenation succeeded, False otherwise
    """
    if not video_list:
        logging.error("No video files provided for concatenation")
        return False
        
    if not all(isinstance(v, str) for v in video_list):
        logging.error("Invalid video path format in input list")
        return False

    clips = []
    try:
        # Load and validate clips
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

def validate_video_file(video_path: str) -> bool:
    """
    Quick validation of video file integrity.
    
    Args:
        video_path: Path to video file to validate
        
    Returns:
        bool: True if video appears valid
    """
    try:
        with VideoFileClip(video_path) as clip:
            return clip.duration > 0
    except Exception:
        return False

if __name__ == "__main__":
    # Example test code
    test_videos = [
        "final_videos/section_0.mp4",
        "final_videos/section_1.mp4"
    ]
    
    existing_videos = [v for v in test_videos if os.path.exists(v)]
    
    if concatenate_videos(existing_videos, "final_videos/test_output.mp4"):
        print("Test concatenation successful")
    else:
        print("Test concatenation failed")
