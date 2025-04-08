import os
import json
import time
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List

from script_generation import generate_script, save_script
from text_animation import create_text_animation_video, overlay_text_on_video
import d3_generator
from generate_interactive_page import generate_interactive_final_page
from moviepy.editor import VideoFileClip, AudioFileClip
from generate_video import concatenate_videos, validate_video_file

# Configure system for UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Constants
BACKGROUND_VIDEO = "videos/background.mp4"
MAX_RETRIES = 3
WORKER_TIMEOUT = 300  # 5 minutes per section

def cleanup_previous_run():
    """Clean up all previous output files before new run"""
    print("🧹 Cleaning up previous run files...")
    
    dirs_to_clear = [
        "audio",
        "final_videos",
        "d3_visualizations",
        "temp_files"
    ]
    
    files_to_clear = [
        "output_script.json",
        "interactive_page.html",
        "d3_standalone.html"
    ]
    
    # Clean directories
    for directory in dirs_to_clear:
        if os.path.exists(directory):
            for attempt in range(3):  # Retry mechanism
                try:
                    shutil.rmtree(directory)
                    print(f"✓ Cleared directory: {directory}")
                    break
                except Exception as e:
                    print(f"⚠️ Failed to clear {directory} (attempt {attempt+1}): {e}")
                    time.sleep(1)
        os.makedirs(directory, exist_ok=True)
    
    # Clean individual files
    for file in files_to_clear:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✓ Removed file: {file}")
            except Exception as e:
                print(f"⚠️ Could not delete {file}: {e}")

def process_section(section_index: int, section: Dict) -> str:
    """Process individual section with enhanced error handling"""
    start_time = time.time()
    print(f"\n🚀 Processing section {section_index} - {section.get('title', '')}")
    
    # Audio generation
    audio_filename = f"audio_section_{section_index}.mp3"
    audio_path = os.path.join("audio", audio_filename)
    
    # Generate fresh audio each time (since we cleaned the directory)
    from text_to_speech import generate_audio
    audio_path = generate_audio(section["text"], section_index)
    if not audio_path:
        print(f"❌ Audio generation failed for section {section_index}")
        return None

    # Get duration from audio
    try:
        with AudioFileClip(audio_path) as audio_clip:
            duration = audio_clip.duration
            print(f"⏱️ Audio duration: {duration:.2f}s")
    except Exception as e:
        print(f"❌ Could not get audio duration: {e}")
        return None

    # Text animation
    text_anim_path = f"temp_files/text_anim_{section_index}.mp4"
    print("🖌️ Generating text animation...")
    if not create_text_animation_video(
        section["text"], 
        (854, 720),
        duration,
        output_path=text_anim_path,
        font_size=32
    ):
        print(f"❌ Text animation failed")
        return None

    # Final video composition
    video_output_path = f"final_videos/section_{section_index}.mp4"
    print("🎥 Composing final video...")
    if not overlay_text_on_video(
        None,
        section["text"],
        video_output_path,
        BACKGROUND_VIDEO if os.path.exists(BACKGROUND_VIDEO) else None,
        audio_path,
        text_anim_path
    ):
        print(f"❌ Video composition failed")
        return None

    # Cleanup temp files
    try:
        if os.path.exists(text_anim_path):
            os.remove(text_anim_path)
    except Exception as e:
        print(f"⚠️ Could not clean up temp file: {e}")

    print(f"✅ Completed section {section_index} in {time.time()-start_time:.2f}s")
    return video_output_path

def generate_final_outputs(script: Dict) -> bool:
    """Generate all final outputs with progress tracking"""
    # Generate D3 visualizations in parallel
    print("\n📊 Generating D3 visualizations...")
    d3_process = subprocess.Popen(["python", "d3_generator.py"])
    
    # Process video sections
    print("\n🎬 Processing video sections...")
    video_paths = []
    with ProcessPoolExecutor(max_workers=min(8, len(script["sections"]))) as executor:
        futures = {
            executor.submit(process_section, i, section): i 
            for i, section in enumerate(script["sections"])
        }
        
        for future in as_completed(futures):
            idx = futures[future]
            try:
                result = future.result(timeout=WORKER_TIMEOUT)
                if result:
                    video_paths.append(result)
                    print(f"✅ Section {idx} completed successfully")
                else:
                    print(f"❌ Section {idx} failed")
            except Exception as e:
                print(f"❌ Section {idx} timed out or crashed: {e}")

    # Concatenate videos
    if video_paths:
        complete_video_path = os.path.join("final_videos", "complete_video.mp4")
        print(f"\n🔗 Concatenating {len(video_paths)} sections...")
        if not concatenate_videos(sorted(video_paths), complete_video_path):
            print("❌ Video concatenation failed")
            return False

    # Wait for D3 to finish
    try:
        print("\n⏳ Waiting for D3 generation to complete...")
        d3_process.wait(timeout=300)
    except subprocess.TimeoutExpired:
        print("⚠️ D3 generation timed out")

    # Generate interactive page
    print("\n🌐 Generating interactive page...")
    if not generate_interactive_final_page(script):
        print("❌ Interactive page generation failed")
        return False

    return True

def main(topic=None):
    # Clear all previous outputs before starting
    cleanup_previous_run()
    
    if not topic:
        topic = input("Enter topic: ").strip()
        if not topic:
            print("❌ No topic provided")
            return

    print("\n📝 Generating script...")
    script = generate_script(topic)
    if not script or not script.get("sections"):
        print("❌ Script generation failed")
        return

    save_script(script)
    print(f"\n📚 Generated {len(script['sections'])} sections")

    if generate_final_outputs(script):
        print("\n🎉 Generation Complete!\n")
        print("Output Files:")
        print("- interactive_page.html")
        print("- d3_standalone.html")
        print("- final_videos/complete_video.mp4")
    else:
        print("\n❌ Generation completed with errors\n")

if __name__ == "__main__":
    # Accept topic from command-line argument if provided
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    else:
        topic = None
    main(topic)
