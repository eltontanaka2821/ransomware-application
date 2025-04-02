from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from rbprof import BehaviorEngine
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

engine = BehaviorEngine()

def safe_analyze(filepath):
    """Wrapper to ensure analysis results are always properly formatted"""
    try:
        result = engine.analyze(filepath)
        
        # Ensure result is a dictionary and properly structured
        if not isinstance(result, dict):
            result = {'status': 'error', 'error': 'Invalid result format'}
        
        # Add filename if not present
        if 'filename' not in result:
            result['filename'] = os.path.basename(filepath)
            
        # Validate nested structures (prevent "string indices must be integers")
        if 'events' in result and isinstance(result['events'], list):
            for event in result['events']:
                if not isinstance(event, dict):
                    result['status'] = 'error'
                    result['error'] = 'Event data must be a dictionary'
                    break
        
        return result
    except Exception as e:
        return {
            'status': 'error',
            'error': f"Analysis failed: {str(e)}",
            'filename': os.path.basename(filepath),
            'debug_info': str(e.__class__.__name__)  # Helps diagnose the issue
        }

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            result = safe_analyze(filepath)
            
            # Ensure JSON serialization works
            try:
                json_result = json.dumps(result, indent=2, default=str)  # Handles datetime
                result = json.loads(json_result)  # Convert back to dict
            except Exception as e:
                result = {
                    'status': 'error',
                    'error': f"Result serialization failed: {str(e)}",
                    'filename': filename
                }
            
            # Save results with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_filename = f"result_{timestamp}_{filename}.json"
            result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
            
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            return render_template('results.html', result=result)
    
    return render_template('upload.html')

@app.route('/results/<result_file>')
def show_results(result_file):
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_file)
    
    if not os.path.exists(result_path):
        flash('Results not found')
        return redirect(url_for('upload_file'))
    
    try:
        with open(result_path, 'r') as f:
            result = json.load(f)
        
        # Validate loaded result
        if not isinstance(result, dict):
            result = {'status': 'error', 'error': 'Invalid result format'}
        
        return render_template('results.html', result=result)
    except Exception as e:
        return render_template('results.html', 
                            result={
                                'status': 'error',
                                'error': f'Could not load results: {str(e)}'
                            })

if __name__ == '__main__':
    app.run(debug=True)