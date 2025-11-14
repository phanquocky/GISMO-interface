import os
import subprocess
from flask import Blueprint, render_template, request, current_app, flash, send_from_directory, send_file, abort
from werkzeug.utils import secure_filename
from .forms import InputForm
from .utils.parse_gismo_output import parse_sensor_set_from_gismo_output
import datetime

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    form = InputForm()
    sensor = ''
    output=''
    gismo_output= None
    download_files = []


    if form.validate_on_submit():
        network_file = None
        # k parameter (default 1)
        try:
            k_val = int(form.k.data) if getattr(form, 'k', None) is not None else 1
        except Exception:
            k_val = 1
        if k_val < 1:
            k_val = 1

        print(f"Using k = {k_val}")

        # 1. If file uploaded
        if form.file.data:
            file = form.file.data
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext.lstrip('.')}"
            network_file = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(network_file)

        # 2. If content provided
        elif form.content.data.strip():
            # generate unique filename based on date-time
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"input_{timestamp}.txt"
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            network_file = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # write the content to the file
            with open(network_file, 'w', encoding='utf-8') as f:
                f.write(form.content.data)

        else:
            flash("Please provide a file or paste some content.", 'error')
            return render_template('index.html', form=form)

        print(f"Input file path: {network_file}")
        for k in range(1, k_val + 1):
            print(f"Processing for k = {k}...")
            # run cnf command
            try:
                cnf_file =  f"output_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.cnf"
                result = subprocess.run(['python3', './identifying-codes/scripts/encoding/encode_network.py', '-n', network_file, '--out_dir', current_app.config['UPLOAD_FOLDER'], '--out_file', cnf_file, '--encoding', 'gis', '--two_step', '-k', str(k)],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True)
                output = result.stdout

                # If the encode script created the expected file inside the 'k{n}' subfolder, expose it for download
                possible_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'k{k}', cnf_file)
                if os.path.isfile(possible_path):
                    download_files.append(possible_path)

            except subprocess.CalledProcessError as e:
                output = f"Error running encode_network.py:\n{e.stderr}"
            
            print("Output: ", output)
            # Run ./gismo command
            try:
                input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"k{k}/{cnf_file}")
                result = subprocess.run(['./gismo/build/gismo',input_path],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True)
                gismo_output = result.stdout

                # parse gismo output to get sensor set
            
                sensor_S = parse_sensor_set_from_gismo_output(gismo_output, input_path)
                # change sensor_S to string for display
                print(f"Sensor set for k={k}: {sensor_S}")
                sensor += f"\nGeneralised identifying code set (k = {k}): {sensor_S}\n"
            except subprocess.CalledProcessError as e:
                gismo_output = f"Error running gismo:\n{e.stderr}"
            print("GiSMo Output: ", gismo_output)

        # clean TEMP_ files in current folder
        try:
            for f in os.listdir('.'):
                if f.startswith('TEMP_'):
                    os.remove(f)
        except Exception as e:
            print(f"Error cleaning TEMP_ files: {e}")

    else:
        print("Form not validated or not submitted yet.")
    return render_template('index.html', form=form, output=output, sensor=sensor, download_files=download_files)


@bp.route('/download_cnf/<path:filepath>', methods=['GET'])
def download_cnf(filepath):
    """Serve a file path under the uploads folder.

    Example: GET /download_cnf/uploads/k1/output.cnf
    The provided filepath is resolved relative to the project root and must
    be located inside the configured UPLOAD_FOLDER to be served.
    """
    project_root = os.path.dirname(current_app.root_path)
    uploads_root = os.path.abspath(os.path.join(project_root, current_app.config['UPLOAD_FOLDER']))

    # Normalize the incoming path and resolve absolute path
    # If client sends a leading '/', strip it so we join relative to project_root
    candidate = filepath.lstrip('/')
    file_path = os.path.abspath(os.path.join(project_root, candidate))
    current_app.logger.debug("Requested download path: %s", file_path)

    # Ensure the resolved file path is inside the uploads directory for safety
    if not file_path.startswith(uploads_root + os.sep):
        current_app.logger.warning("Attempt to access file outside uploads: %s", file_path)
        abort(403)

    if not os.path.isfile(file_path):
        current_app.logger.debug("File not found: %s", file_path)
        abort(404)

    # Use send_file with as_attachment to serve the exact file path
    return send_file(file_path, as_attachment=True, mimetype='text/plain')