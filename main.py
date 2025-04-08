from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import subprocess
import os
import threading
import time
import json
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')

# Track generation status
generation_status = {
    'in_progress': False,
    'completed': False,
    'topic': None,
    'progress': 0,
    'message': '',
    'start_time': None
}

def simulate_generation(topic):
    global generation_status
    generation_status['in_progress'] = True
    generation_status['completed'] = False
    generation_status['topic'] = topic
    generation_status['progress'] = 0
    generation_status['message'] = 'Starting simulation...'
    generation_status['start_time'] = datetime.now()
    
    try:
        # Simulate 2 minutes of generation time
        while (datetime.now() - generation_status['start_time']).total_seconds() < 120:
            elapsed = (datetime.now() - generation_status['start_time']).total_seconds()
            progress = min(100, int((elapsed / 120) * 100))
            
            generation_status['progress'] = progress
            generation_status['message'] = f"Simulating generation ({progress}%)"
            
            # Simulate different stages
            if progress < 30:
                generation_status['message'] = "Preparing content..."
            elif progress < 60:
                generation_status['message'] = "Generating visuals..."
            elif progress < 90:
                generation_status['message'] = "Rendering video..."
            else:
                generation_status['message'] = "Finalizing output..."
            
            time.sleep(1)  # Update every second
        
        generation_status['completed'] = True
        generation_status['message'] = 'Simulation complete!'
        generation_status['progress'] = 100
        
    except Exception as e:
        print("Error in simulation:", str(e))
        generation_status['message'] = f'Error: {str(e)}'
    finally:
        generation_status['in_progress'] = False

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/video')
def video():
    return render_template('video.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    topic = data.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    if generation_status['in_progress']:
        return jsonify({'error': 'Generation already in progress'}), 429
    
    # Start simulation in background
    thread = threading.Thread(target=simulate_generation, args=(topic,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'processing',
        'message': 'Video generation simulation started (2 minutes)'
    })

@app.route('/progress')
def progress():
    def generate():
        while True:
            data = {
                "status": "in_progress" if generation_status['in_progress'] else "error",
                "progress": generation_status['progress'],
                "message": generation_status['message'],
                "estimated_time": max(0, 120 - (datetime.now() - generation_status['start_time']).total_seconds()) if generation_status['start_time'] else 120
            }
            
            if generation_status['completed']:
                data["status"] = "completed"
                yield f"data: {json.dumps(data)}\n\n"
                break
            else:
                yield f"data: {json.dumps(data)}\n\n"
            
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/interactive')
def interactive():
    # Always show the interactive page (using pre-generated content)
    return render_template('interactive_page.html', 
                         topic=generation_status.get('topic', 'Sample Topic'))

if __name__ == '__main__':
    app.run(debug=True, threaded=True)