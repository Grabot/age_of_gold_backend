from app.config import Config
from app.routes.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm
from app.routes.logins.github_login import github_login
from app.routes.logins.google_login import google_login
from app.routes.logins.reddit_login import reddit_login
from flask import redirect, url_for, render_template
from flask import flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
import base64

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def set_routes(app):
    google_login(app)
    github_login(app)
    reddit_login(app)

    @app.route('/upload')
    def upload_form():
        return render_template('upload.html')

    @app.route('/upload', methods=['POST'])
    def upload_image():
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(Config.UPLOAD_FOLDER, filename))
            # print('upload_image filename: ' + filename)
            flash('Image successfully uploaded and displayed below')
            return render_template('upload.html', filename=filename)
        else:
            flash('Allowed image types are -> png, jpg, jpeg, gif')
            return redirect(request.url)

    @app.route("/api/avatar/<filename>")
    def image_as_html(filename):
        with open('/app/static/uploads/%s' % filename, 'rb') as fd:
            image_as_base64_html = f"""
           <img src="data:image/png;base64,{base64.encodebytes(fd.read()).decode()}">"""

        return image_as_base64_html
