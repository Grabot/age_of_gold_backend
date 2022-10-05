from flask import render_template, flash, redirect
from app.routes.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user


def set_routes(app):

    from flask_login import login_required

    @app.route('/')
    @app.route('/index')
    @login_required
    def home():
        posts = [
            {
                'author': {'username': 'John'},
                'body': 'Beautiful day in Portland!'
            },
            {
                'author': {'username': 'Susan'},
                'body': 'The Avengers movie was so cool!'
            }
        ]
        return render_template("index.html", title='Home Page', posts=posts)

    from app.models.user import User

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect('/')
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.verify_password(form.password.data):
                flash('Invalid username or password')
                return redirect('/login')
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', title='Sign In', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect('/')

    from app import db

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect('/')
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.hash_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Congratulations, you are now a registered user!')
            return redirect('/login')
        return render_template('register.html', title='Register', form=form)

