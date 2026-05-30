from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from rag_engine import RAGEngine
from video_processor import VideoProcessor
import os
import json
import pickle
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Initialize engines
rag_engine = RAGEngine()
video_processor = VideoProcessor()

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data/videos', exist_ok=True)
os.makedirs('data/audios', exist_ok=True)
os.makedirs('data/jsons', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/mode', methods=['GET'])
def get_mode():
    """Check if running in production or local mode."""
    return jsonify({
        'mode': 'production' if os.environ.get('RENDER', False) else 'local',
        'llm': 'OpenAI' if os.environ.get('RENDER', False) else 'Ollama'
    })

@app.route('/')
def serve_frontend():
    """Serve the main HTML file."""
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Process a question and return answer with references."""
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Please enter a question'}), 400
    
    if rag_engine.df is None:
        return jsonify({'error': 'No course content loaded. Please process videos first.'}), 400
    
    result = rag_engine.process_query(query)
    return jsonify(result)

@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Upload and process a video file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Get video metadata
    video_number = request.form.get('number', '1')
    video_title = request.form.get('title', 'Untitled')
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    video_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(video_path)
    
    # Process video
    result = video_processor.process_video(video_path, video_number, video_title)
    
    if result['success']:
        # Rebuild index after adding new video
        rebuild_index()
        return jsonify({'success': True, 'message': 'Video processed successfully', 'data': result})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Processing failed')}), 500

@app.route('/api/rebuild-index', methods=['POST'])
def rebuild_index():
    """Rebuild the search index from all JSON files."""
    try:
        jsons_dir = "data/jsons"
        if not os.path.exists(jsons_dir):
            return jsonify({'error': 'No JSON files found'}), 400
        
        json_files = [f for f in os.listdir(jsons_dir) if f.endswith('.json')]
        
        if not json_files:
            return jsonify({'error': 'No JSON files found'}), 400
        
        my_dicts = []
        chunk_id = 0
        
        for json_file in json_files:
            with open(f"{jsons_dir}/{json_file}", 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Generate embeddings for chunks
            texts = [chunk['text'] for chunk in content['chunks']]
            embeddings = rag_engine.create_embedding(texts)
            
            for i, chunk in enumerate(content['chunks']):
                chunk['chunk_id'] = chunk_id
                if embeddings and i < len(embeddings):
                    chunk['embedding'] = embeddings[i]
                my_dicts.append(chunk)
                chunk_id += 1
        
        # Save index
        with open("data/index.pkl", "wb") as f:
            pickle.dump(my_dicts, f)
        
        # Reload index
        rag_engine.load_index()
        
        return jsonify({'success': True, 'message': f'Index rebuilt with {chunk_id} chunks'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status."""
    return jsonify({
        'index_loaded': rag_engine.df is not None,
        'chunks_count': len(rag_engine.df) if rag_engine.df is not None else 0,
        'models': {
            'embedding': rag_engine.embedding_model,
            'llm': rag_engine.llm_model
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)