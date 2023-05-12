from flask import render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user

from app.blueprints.main import bp
from app.utils import render
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
        user = api_client.users.verify(username, password)
        if user is None:
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('main.login'))
        login_user(user, remember=remember)
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
