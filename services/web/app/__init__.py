from flask import Flask

from app.config import settings


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(settings.dict())

    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.users import bp as users_bp
    app.register_blueprint(users_bp,  url_prefix='/users')

    from app.blueprints.sources import bp as posts_bp
    app.register_blueprint(posts_bp, url_prefix='/sources')

    return app
