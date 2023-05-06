from flask import render_template

from app.blueprints.main import bp


@bp.route('/')
def index():
    return render_template('main/index.html')


@bp.route('/profile')
def profile():
    return 'Profile'
