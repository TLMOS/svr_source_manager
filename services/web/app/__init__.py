from flask import Flask
from flask_login import LoginManager, UserMixin

from app.config import settings


class WebUiUser(UserMixin):
    id: int = 1
    username: str = 'web ui user'


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(settings.dict())

    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return WebUiUser()

    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.security import bp as security_bp
    app.register_blueprint(security_bp, url_prefix='/security')

    from app.blueprints.sources import bp as posts_bp
    app.register_blueprint(posts_bp, url_prefix='/sources')

    from app.blueprints.search import bp as search_bp
    app.register_blueprint(search_bp, url_prefix='/search')

    return app
