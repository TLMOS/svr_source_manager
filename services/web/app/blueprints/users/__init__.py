from flask import Blueprint

bp = Blueprint('users', __name__)


from app.blueprints.users import routes
