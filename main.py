
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from rbprof import BehaviorEngine
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

engine = BehaviorEngine()

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
            
            
            result = engine.analyze(filepath)
            
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_filename = f"result_{timestamp}_{filename}.json"
            result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
            
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            return render_template('results.html', 
                                filename=filename,
                                result=result,
                                result_file=result_filename)
    
    return render_template('upload.html')

@app.route('/results/<result_file>')
def show_results(result_file):
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_file)
    
    if not os.path.exists(result_path):
        flash('Results not found')
        return redirect(url_for('upload_file'))
    
    with open(result_path, 'r') as f:
        result = json.load(f)
    
    filename = result_file.split('_', 2)[-1].rsplit('.', 1)[0]
    
    return render_template('results.html', 
                         filename=filename,
                         result=result,
                         result_file=result_file)

if __name__ == '__main__':
    app.run(debug=True)