from flask import Blueprint

bp = Blueprint('security', __name__)


from app.blueprints.security import routes
