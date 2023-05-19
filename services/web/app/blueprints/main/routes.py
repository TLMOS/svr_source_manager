from urllib.error import HTTPError

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user

from app.blueprints.main import bp
from app import WebUiUser
from app.clients import core_api


@bp.route('/')
def index():
    return render_template('main/index.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        try:
            if core_api.security.verify_password(password):
                login_user(WebUiUser(), remember=remember)
                if not core_api.rabbitmq.is_opened():
                    core_api.rabbitmq.startup(password)
            else:
                flash('Incorrect password.', 'error')
                return redirect(url_for('main.login'))
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
