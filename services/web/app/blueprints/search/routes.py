from flask import request, flash
from flask_login import login_required

from app.blueprints.search import bp
from app.clients import core_api
from app.logic import action, render


@bp.before_request
@login_required
def before_request():
    pass


@bp.route('/', methods=['GET', 'POST'])
@render(template='search/index.html', endpoint='sources.index')
def index():
    is_opened = core_api.rabbitmq.is_opened()
    return {
        'is_opened': is_opened
    }


@bp.route('/rabbitmq/set_credentials', methods=['POST'])
@action(endpoint='search.index')
def rabbitmq_set_credentials():
    password = request.form['password']
    rabbitmq_username = request.form['rabbitmq_username']
    rabbitmq_password = request.form['rabbitmq_password']
    if password == '':
        flash(message='Password can\'t be empty.', category='error')
    if rabbitmq_username == '' or rabbitmq_password == '':
        flash(message='Got empty credentials.', category='error')
    elif not core_api.security.verify_password(password):
        flash(message='Incorrect password.', category='error')
    else:
        core_api.rabbitmq.set_credentials(rabbitmq_username, rabbitmq_password,
                                          password)


@bp.route('/rabbitmq/start', methods=['POST'])
@action(endpoint='search.index')
def rabbitmq_start():
    password = request.form['password']
    if password == '':
        flash(message='Password can\'t be empty.', category='error')
    elif not core_api.security.verify_password(password):
        flash(message='Incorrect password.', category='error')
    else:
        core_api.rabbitmq.startup(password)


@bp.route('/rabbitmq/stop', methods=['POST'])
@action(endpoint='search.index')
def rabbitmq_stop():
    core_api.rabbitmq.shutdown()
