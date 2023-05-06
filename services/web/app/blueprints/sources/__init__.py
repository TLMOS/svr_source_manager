from flask import Blueprint

bp = Blueprint('sources', __name__)


from app.blueprints.sources import routes
