import os

def generate_interactive_final_page(script_data, output_path="templates/interactive_page.html"):
    try:
        sections = script_data.get("sections", [])
        total_sections = len(sections)

        # Ensure all D3 visualization files exist
        for i in range(1, total_sections + 1):
            d3_file = os.path.join("d3_visualizations", f"section_{i}.html")
            if not os.path.exists(d3_file):
                raise FileNotFoundError(f"D3 file not found: {d3_file}")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Interactive Learning Page</title>
    <style>
        body {{ margin: 0; padding: 0; }}
        #container {{ display: flex; height: 100vh; }}
        video, iframe {{ width: 50%; height: 100%; border: none; }}
        #controls {{
            position: fixed;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
        }}
        button {{
            padding: 10px 20px;
            margin: 0 5px;
            font-size: 16px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
<div id="container">
    <video id="video" controls>
        <source src="final_videos/complete_video.mp4" type="video/mp4">
    </video>
    <iframe id="d3-frame" src="d3_visualizations/section_1.html"></iframe>
</div>
<div id="controls">
    <button onclick="prevSection()">⬅️ Previous</button>
    <button onclick="nextSection()">Next ➡️</button>
</div>
<script>
    let currentSection = 0;
    const totalSections = {total_sections};
    function updateD3() {{
        document.getElementById('d3-frame').src = `d3_visualizations/section_${{currentSection+1}}.html`;
    }}
    function nextSection() {{
        if (currentSection < totalSections - 1) {{
            currentSection++;
            updateD3();
        }}
    }}
    function prevSection() {{
        if (currentSection > 0) {{
            currentSection--;
            updateD3();
        }}
    }}
</script>
</body>
</html>"""

        # Write the interactive page to the templates folder
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"✅ Interactive page generated at {output_path}")
        return html_content
    except Exception as e:
        print(f"❌ Error generating interactive page: {e}")
        return None
