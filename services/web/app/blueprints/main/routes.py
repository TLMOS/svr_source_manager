from urllib.error import HTTPError

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user

from app.blueprints.main import bp
from app.logic import render
from app import api_client


@bp.route('/')
def index():
    return render_template('main/index.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        try:
            user = api_client.users.verify(username, password)
            if user is None:
                flash('Incorrect username or password.', 'error')
                return redirect(url_for('main.login'))
            login_user(user, remember=remember)
        except HTTPError as e:
            flash(f'HTTPError: {e.status} {e.msg}', 'error')
        return redirect(url_for('main.index'))
    else:
        return render_template('main/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/profile')
@login_required
@render(template='main/profile.html', endpoint='main.profile')
def profile():
    return {}
