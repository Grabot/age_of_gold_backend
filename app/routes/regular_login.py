from flask import render_template, flash, redirect, request
from app.routes.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm
from flask_login import current_user, login_user, logout_user
from datetime import datetime


def regular_login(app):

    from flask_login import login_required

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
            return redirect('/index')
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.verify_password(form.password.data):
                flash('Invalid username or password')
                return redirect('/login')
            login_user(user, remember=form.remember_me.data)
            return redirect('/index')
        return render_template('login.html', title='Sign In', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect('/index')

    from app import db

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect('/index')
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.hash_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Congratulations, you are now a registered user!')
            return redirect('/login')
        return render_template('register.html', title='Register', form=form)

    @app.route('/user/<username>')
    @login_required
    def user(username):
        user = User.query.filter_by(username=username).first_or_404()
        posts = [
            {'author': user, 'body': 'Test post #1'},
            {'author': user, 'body': 'Test post #2'}
        ]
        form = EmptyForm()
        return render_template('user.html', user=user, posts=posts, form=form)

    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()

    @app.route('/edit_profile', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        form = EditProfileForm(current_user.username)
        if form.validate_on_submit():
            current_user.username = form.username.data
            current_user.about_me = form.about_me.data
            db.session.commit()
            flash('Your changes have been saved.')
            return redirect('/edit_profile')
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.about_me.data = current_user.about_me
        return render_template('edit_profile.html', title='Edit Profile', form=form)

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.route('/follow/<username>', methods=['POST'])
    @login_required
    def follow(username):
        form = EmptyForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=username).first()
            if user is None:
                flash('User {} not found.'.format(username))
                return redirect('/index')
            if user == current_user:
                flash('You cannot follow yourself!')
                return redirect('/user/%s' % username)
            current_user.befriend(user)
            user.befriend(current_user)
            db.session.commit()
            flash('You are following {}!'.format(username))
            return redirect('/user/%s' % username)
        else:
            return redirect('/index')

    @app.route('/unfollow/<username>', methods=['POST'])
    @login_required
    def unfollow(username):
        form = EmptyForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=username).first()
            if user is None:
                flash('User {} not found.'.format(username))
                return redirect('/index')
            if user == current_user:
                flash('You cannot unfollow yourself!')
                return redirect('/user/%s' % username)
            # unfriending is only one way. The other friend will still think they are friends but can't message them
            current_user.unfriend(user)
            db.session.commit()
            flash('You are not following {}.'.format(username))
            return redirect('/user/%s' % username)
        else:
            return redirect('/index')

