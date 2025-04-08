import google.generativeai as genai
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    sys.exit("❌ Missing Gemini API Key")
genai.configure(api_key=GEMINI_API_KEY)

# Ensure the output directory exists
OUTPUT_DIR = "d3_visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_response(text):
    """Clean response text: remove markdown formatting and extra prompt instructions."""
    try:
        text = re.sub(r"```(html)?", "", text)
        text = re.sub(r"```", "", text)
        return text.strip()
    except Exception as e:
        print(f"❌ Error cleaning response: {e}")
        return text.strip()

def generate_d3_prompt(section_text, visualization_type):
    """
    Generate a detailed humanized prompt for creating a D3.js animation.
    The prompt is at least 100 words and based on the section content.
    """
    try:
        base_prompt = (
            f"Based on the following section content:\n\n\"{section_text}\"\n\n"
            f"and considering the visualization type \"{visualization_type}\", "
            "generate a detailed, humanized prompt for creating an interactive D3.js animation demonstration. "
            "This animation should allow manual movement and interactions with elements to demonstrate the underlying concepts. "
            "Describe in detail how the elements should appear, move, and interact. Include instructions about transitions, scaling, "
            "dynamic updates, design aspects, color schemes, and effects like easing or delays. "
            "Ensure the prompt is very detailed (at least 100 words) and guides the code generation process to produce clean, well-structured, "
            "and optimized HTML and JavaScript code for D3.js, tailored to the subject matter. "
            "The output should be only code in HTML format, without any extra explanation or markdown formatting."
        )
        words = base_prompt.split()
        if len(words) < 100:
            extra = (
                " Additionally, include instructions for user interactivity, error handling, and performance optimization. "
                "The prompt should be elaborate and comprehensive to ensure robust, production-ready code."
            )
            base_prompt += extra
        return base_prompt
    except Exception as e:
        print(f"❌ Error generating D3 prompt: {e}")
        return ""

def generate_d3_code(prompt):
    """
    Use Gemini 2.5 Pro experimental model to generate D3.js HTML code based on the provided prompt.
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")
        response = model.generate_content(prompt)
        return clean_response(response.text)
    except Exception as e:
        print(f"❌ Error in generating D3 code: {e}")
        return None

def review_and_optimize_code(generated_code):
    """
    Use Gemini 2.0 Flash model to review and optimize the generated D3.js code.
    The review prompt instructs the model to output only the final corrected code in HTML without any extra text.
    """
    try:
        review_prompt = (
            "Review the following D3.js HTML code for any errors and optimization opportunities. "
            "If you find errors, provide the corrected and optimized version of the code, outputting only the final code. "
            "Do not include any extra explanations, markdown formatting, or comments in your output. "
            "If the code is already optimized and error-free, simply respond with 'CODE_OPTIMIZED'.\n\n"
            f"Code:\n{generated_code}\n\nOutput:"
        )
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(review_prompt)
        reviewed = clean_response(response.text)
        if "code_optmized" in reviewed.lower() or "code is optimized" in reviewed.lower() or "CODE_OPTIMIZED" in reviewed:
            return generated_code
        else:
            return reviewed
    except Exception as e:
        print(f"❌ Error in reviewing D3 code: {e}")
        return generated_code

def save_html(section_index, html_code):
    """
    Save the generated HTML code for a section to a separate file in the OUTPUT_DIR.
    """
    filename = os.path.join(OUTPUT_DIR, f"section_{section_index+1}.html")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_code)
        print(f"✅ Section {section_index+1} HTML saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving file {filename}: {e}")

def process_section(i, section):
    """Process a single section: generate prompt, code, review and save HTML."""
    try:
        section_text = section.get("text", "")
        viz_type = section.get("visualization_type", "default")
        print(f"Processing section {i+1} with visualization type '{viz_type}'...")
        
        # Generate prompt for code generation
        d3_prompt = generate_d3_prompt(section_text, viz_type)
        if not d3_prompt:
            print(f"❌ Failed to generate prompt for section {i+1}")
            return False
        
        # Generate D3 code using Gemini 2.5 Pro
        generated_code = generate_d3_code(d3_prompt)
        if not generated_code:
            print(f"❌ Failed to generate D3 code for section {i+1}")
            return False
        
        # Review and optimize code using Gemini 2.0 Flash
        final_code = review_and_optimize_code(generated_code)
        if not final_code:
            print(f"❌ Failed to review/optimize code for section {i+1}")
            return False
        
        # Save final HTML code for the section
        save_html(i, final_code)
        return True
    except Exception as e:
        print(f"❌ Unexpected error in processing section {i+1}: {e}")
        return False

def main():
    try:
        with open("output_script.json", "r", encoding="utf-8") as f:
            script_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading output_script.json: {e}")
        return

    sections = script_data.get("sections", [])
    if not sections:
        print("❌ No sections found in output_script.json")
        return

    # Process sections concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(sections)) as executor:
        futures = [executor.submit(process_section, i, section) for i, section in enumerate(sections)]
        for future in as_completed(futures):
            # Simply wait for all to complete; individual errors are already printed.
            future.result()

if __name__ == "__main__":
    main()
