import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, CompositeVideoClip, AudioFileClip, 
    ColorClip, concatenate_videoclips, ImageClip
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[text_animation] %(message)s')

# Configuration
FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf"
FONT_SIZE = 32
FPS = 24
TEXT_AREA_SIZE = (854, 720)
PADDING = 20

def create_text_frame(text, frame_size=TEXT_AREA_SIZE, font_size=FONT_SIZE, padding=PADDING):
    """Create transparent image with wrapped text (max 4 lines)"""
    img = Image.new("RGBA", frame_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except Exception as e:
        logging.warning(f"Could not load truetype font: {e}")
        font = ImageFont.load_default()

    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= frame_size[0] - 2 * padding:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    if len(lines) > 4:
        lines = lines[-4:]
    
    y = padding
    for line in lines:
        draw.text((padding, y), line, font=font, fill="white")
        y += font_size + 10
    
    return np.array(img)

def generate_scrolling_frames(text, frame_size, duration, fps=FPS):
    """Generate frames for typewriter effect with precise timing"""
    total_frames = int(duration * fps)
    full_length = len(text)
    frames = []
    
    for i in range(total_frames):
        fraction = min(i / total_frames, 1.0)
        chars_to_show = int(full_length * fraction)
        subtext = text[:chars_to_show]
        
        frame = create_text_frame(subtext, frame_size)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
        frames.append(frame_rgb)
    
    return frames

def create_text_animation_video(text, frame_size, duration, output_path, font_size=FONT_SIZE):
    """Create text animation video with precise timing and save it to output_path"""
    try:
        logging.info(f"Creating text animation for duration {duration:.2f}s at {output_path}")
        frames = generate_scrolling_frames(text, frame_size, duration)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, FPS, frame_size)
        
        for frame in frames:
            out.write(frame)
        out.release()
        
        if os.path.exists(output_path):
            logging.info("Text animation video created successfully.")
            return output_path
        else:
            logging.error("Text animation video file not found after writing.")
            return None
    except Exception as e:
        logging.error(f"Error creating text animation: {e}")
        return None

def overlay_text_on_video(image_path, text, output_path, background_video_path, audio_path, text_animation_path):
    """Create final composite video by overlaying text animation on background video with proper audio sync"""
    try:
        if not text_animation_path or not os.path.exists(text_animation_path):
            logging.error("Text animation file does not exist.")
            return False

        with AudioFileClip(audio_path) as audio_clip:
            duration = audio_clip.duration
        logging.info(f"Audio duration: {duration:.2f}s")
        
        with VideoFileClip(text_animation_path) as text_clip:
            if text_clip.duration < duration:
                last_frame = text_clip.to_ImageClip().set_duration(duration - text_clip.duration)
                text_clip = concatenate_videoclips([text_clip, last_frame])
            text_clip = text_clip.set_position("center").set_opacity(0.8)
            
            if os.path.exists(background_video_path):
                with VideoFileClip(background_video_path) as bg_clip:
                    bg_clip = bg_clip.resize((1280, 720))
                    if bg_clip.duration < duration:
                        bg_clip = concatenate_videoclips([bg_clip] * (int(duration // bg_clip.duration) + 1))
                    bg_clip = bg_clip.subclip(0, duration)
                    
                    final_clip = CompositeVideoClip([bg_clip, text_clip], use_bgclip=True)
                    with AudioFileClip(audio_path) as audio_clip:
                        final_clip = final_clip.set_audio(audio_clip)
                        final_clip.write_videofile(
                            output_path,
                            fps=FPS,
                            codec="libx264",
                            audio_codec="aac",
                            threads=6,
                            preset='fast',
                            ffmpeg_params=["-movflags", "+faststart"]
                        )
            else:
                bg_clip = ColorClip((1280, 720), color=(0, 0, 0), duration=duration)
                final_clip = CompositeVideoClip([bg_clip, text_clip], use_bgclip=True)
                with AudioFileClip(audio_path) as audio_clip:
                    final_clip = final_clip.set_audio(audio_clip)
                    final_clip.write_videofile(
                        output_path,
                        fps=FPS,
                        codec="libx264",
                        audio_codec="aac",
                        threads=6,
                        preset='fast',
                        ffmpeg_params=["-movflags", "+faststart"]
                    )
        logging.info(f"Final video created at {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating final video: {e}")
        return False

# Optional main() for standalone testing
if __name__ == "__main__":
    test_text = "This is a sample text for the typewriter effect animation demonstration."
    output_anim = "test_text_anim.mp4"
    audio_dummy = "dummy_audio.mp3"  # Provide valid audio if testing overlay
    bg_video = "videos/background.mp4"
    anim_path = create_text_animation_video(test_text, TEXT_AREA_SIZE, 5, output_anim)
    if anim_path:
        overlay_text_on_video(None, test_text, "test_final_video.mp4", bg_video, audio_dummy, anim_path)
