import google.generativeai as genai
import json
import os
import re

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ Missing Gemini API Key")

genai.configure(api_key=GEMINI_API_KEY)

STANDARD_VIZ_TYPES = [
    "inertia_demo", 
    "fma_calculator",
    "action_reaction",
    "comparison_demo"
]

def clean_json(text):
    """Remove markdown code blocks from JSON"""
    return re.sub(r'```json|```', '', text.strip())

def generate_d3_prompt(section_text, viz_type):
    """Generate detailed D3.js prompt for a section"""
    prompt = f"""
    Create a detailed technical prompt for an interactive D3.js visualization that demonstrates concepts from the following educational section:
    
    SECTION TEXT: "{section_text}"
    
    VISUALIZATION TYPE: "{viz_type}"
    
    Requirements:
    - Interactive elements (draggable objects, sliders, etc.)
    - Real-time physics calculations where applicable
    - Clear labels and formulas
    - Visual indicators of forces/movement
    - Responsive design
    - Include both the visualization and explanatory text
    
    The prompt should be at least 100 words and specifically describe:
    - What elements should be visible
    - How user interaction should work
    - What physics/math concepts to visualize
    - How to represent abstract concepts visually
    - Any animations or transitions needed
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Error generating D3 prompt: {e}")
        return None

def generate_script(topic):
    prompt = f"""
    Generate an educational script about '{topic}' with:
    - 5-6 sections (100+ words each)
    - Real-world examples
    - Standard visualization types: {", ".join(STANDARD_VIZ_TYPES)}
    
    Output JSON format:
    {{
        "title": "Title",
        "background_video": "Background description",
        "sections": [
            {{
                "text": "Content...",
                "visualization_type": "inertia_demo",
                "d3_prompt": "Detailed D3 visualization prompt..."
            }}
        ]
    }}
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        script = json.loads(clean_json(response.text))
        
        # Generate D3 prompts for each section
        for section in script["sections"]:
            section["d3_prompt"] = generate_d3_prompt(section["text"], section["visualization_type"])
        
        return script
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def save_script(script):
    if script:
        with open("output_script.json", "w") as f:
            json.dump(script, f, indent=2)
        print("✅ Script saved to output_script.json")

if __name__ == "__main__":
    topic = input("Enter topic: ")
    script = generate_script(topic)
    save_script(script)