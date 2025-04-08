import os
import json
import logging
from gtts import gTTS
from typing import Optional

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Directory setup
SCRIPT_FILE = "output_script.json"
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def generate_audio(text: str, section_index: int, output_dir: str = "audio") -> Optional[str]:
    audio_path = os.path.join(output_dir, f"audio_section_{section_index}.mp3")
    """
    Generate audio file for a section using gTTS with enhanced error handling
    
    Args:
        text: Text content to convert to speech
        section_index: Index of the section for filename
        
    Returns:
        Path to generated audio file or None if failed
    """
    if not text.strip():
        logging.warning(f"Skipping empty text for section {section_index}")
        return None

    audio_path = os.path.join(AUDIO_DIR, f"audio_section_{section_index}.mp3")
    
    try:
        # Check for existing audio first
        if os.path.exists(audio_path):
            logging.info(f"Audio exists for section {section_index}, skipping generation")
            return audio_path

        logging.info(f"Generating audio for section {section_index}...")
        
        tts = gTTS(
            text=text,
            lang='en',
            slow=False,
            lang_check=True
        )
        
        tts.save(audio_path)
        
        # Verify file creation and minimum size (adjust threshold if needed)
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
            raise IOError("Audio file not created or is too small after TTS generation")
            
        logging.info(f"Successfully generated audio: {audio_path}")
        return audio_path

    except Exception as e:
        logging.error(f"Failed to generate audio for section {section_index}: {e}")
        # Clean up partial files
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as ex:
                logging.error(f"Failed to remove partial audio file {audio_path}: {ex}")
        return None

def batch_generate_audio(max_workers: int = 4) -> bool:
    """
    Process all sections from the script file in parallel
    
    Args:
        max_workers: Number of parallel threads for audio generation
        
    Returns:
        True if all audio generated successfully, False otherwise
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if not os.path.exists(SCRIPT_FILE):
        logging.error("Script file not found")
        return False

    try:
        with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
            script_data = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load script: {e}")
        return False

    sections = script_data.get("sections", [])
    if not sections:
        logging.error("No sections found in script")
        return False

    success_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for idx, section in enumerate(sections):
            text = section.get("text", "")
            futures[executor.submit(generate_audio, text, idx)] = idx

        for future in as_completed(futures):
            section_idx = futures[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
                else:
                    logging.error(f"Failed to generate audio for section {section_idx}")
            except Exception as e:
                logging.error(f"Exception in section {section_idx}: {e}")

    total = len(sections)
    logging.info(f"Audio generation complete. Success: {success_count}/{total}")
    return success_count == total

if __name__ == "__main__":
    import sys
    
    workers = 4
    if len(sys.argv) > 1:
        try:
            workers = int(sys.argv[1])
        except ValueError:
            pass
            
    result = batch_generate_audio(max_workers=workers)
    sys.exit(0 if result else 1)
