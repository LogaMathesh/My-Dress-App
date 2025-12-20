from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from celery import Celery
from celery.result import AsyncResult

# Initialize Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Initialize Celery with same config as worker
celery = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files[]')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        task_ids = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                print(f"[FLASK] Uploaded: {filename}")
                
                # Send task to Celery
                task = celery.send_task('tasks.process_image', args=[filepath, filename])
                print(f"[FLASK] Task queued: {task.id}")
                
                task_ids.append({
                    'task_id': task.id,
                    'filename': filename
                })
        
        return jsonify({'tasks': task_ids, 'count': len(task_ids)})
    
    except Exception as e:
        print(f"[FLASK] Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/status/<task_id>')
def task_status(task_id):
    try:
        task = AsyncResult(task_id, app=celery)
        
        print(f"[FLASK] Checking task {task_id}: {task.state}")
        
        response = {
            'state': task.state,
            'status': task.state
        }
        
        if task.state == 'SUCCESS':
            response['result'] = task.result
        elif task.state == 'FAILURE':
            response['error'] = str(task.info)
        
        return jsonify(response)
    
    except Exception as e:
        print(f"[FLASK] Status error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'state': 'ERROR', 'error': str(e)}), 200  # Return 200 with error in JSON

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"[FLASK] 500 Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("[FLASK] Starting Flask server...")
    print(f"[FLASK] Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"[FLASK] Processed folder: {app.config['PROCESSED_FOLDER']}")
    app.run(debug=True, port=5000)