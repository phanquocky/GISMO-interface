import os
import subprocess
from flask import Blueprint, render_template, request, current_app, flash
from werkzeug.utils import secure_filename
from .forms import InputForm
import datetime

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    form = InputForm()
    output = None
    gismo_output= None

    if form.validate_on_submit():
        input_path = None

        # 1. If file uploaded
        if form.file.data:
            file = form.file.data
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext.lstrip('.')}"
            input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(input_path)

        # 2. If content provided
        elif form.content.data.strip():
            # generate unique filename based on date-time
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"input_{timestamp}.txt"
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # write the content to the file
            with open(input_path, 'w', encoding='utf-8') as f:
                f.write(form.content.data)

        else:
            flash("Please provide a file or paste some content.", 'error')
            return render_template('index.html', form=form)

        # run cnf command
        try:
            output_file =  f"output_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.cnf"
            result = subprocess.run(['python3', './identifying-codes/scripts/encoding/encode_network.py', '-n', input_path, '--out_dir', current_app.config['UPLOAD_FOLDER'], '--out_file', output_file, '--encoding', 'gis', '--two_step'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    check=True)
            output = result.stdout

        except subprocess.CalledProcessError as e:
            output = f"Error running encode_network.py:\n{e.stderr}"
        
        # Run ./gismo command
        try:
            input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"k1/{output_file}")
            result = subprocess.run(['./gismo/build/gismo',input_path],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    check=True)
            gismo_output = result.stdout
        except subprocess.CalledProcessError as e:
            gismo_output = f"Error running gismo:\n{e.stderr}"

        # clean TEMP_ files in current folder
        try:
            for f in os.listdir('.'):
                if f.startswith('TEMP_'):
                    os.remove(f)
        except Exception as e:
            print(f"Error cleaning TEMP_ files: {e}")

    return render_template('index.html', form=form, output=output, gismo_output=gismo_output)