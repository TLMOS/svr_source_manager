from flask import Flask
from flask_login import LoginManager

from app.config import settings
from app import api_client


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(settings.dict())

    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return api_client.users.get(user_id)

    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.users import bp as users_bp
    app.register_blueprint(users_bp,  url_prefix='/users')

    from app.blueprints.sources import bp as posts_bp
    app.register_blueprint(posts_bp, url_prefix='/sources')

    return app
