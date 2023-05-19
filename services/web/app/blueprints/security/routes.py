from flask import request
from flask_login import login_required

from app.blueprints.security import bp
from app.logic import render, action, flash, session
from app.clients import core_api


@bp.before_request
@login_required
def before_request():
    pass


@bp.route('/')
@render(template='security/index.html', endpoint='security.index')
def index():
    if 'tmp' in session:
        token = session['tmp']
        del session['tmp']
        return {
            'token': token
        }


@bp.route('/update_password', methods=['POST'])
@action(endpoint='security.index')
def update_password():
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    confirm_new_password = request.form['confirm_new_password']
    if new_password == '':
        flash(message='New password can\'t be empty.', category='error')
    elif new_password != confirm_new_password:
        flash(message='Passwords don\'t match.', category='error')
    elif old_password == new_password:
        flash(message='New password must be different from old one.',
              category='error')
    elif core_api.security.verify_password(old_password):
        core_api.security.update_password(new_password)
    else:
        flash(message='Incorrect password.', category='error')


@bp.route('/update_token', methods=['POST'])
@action(endpoint='security.index')
def update_token():
    session['tmp'] = core_api.security.update_token()


@bp.route('/invalidate_token', methods=['POST'])
@action(endpoint='security.index')
def invalidate_token():
    core_api.security.invalidate_token()
