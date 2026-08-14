import os
import config as cfg
from flask import Flask


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", cfg.SECRET_KEY),
        DATABASE=os.environ.get("DATABASE", cfg.DB_PATH),
        ARTICLES_PER_PAGE=cfg.ARTICLES_PER_PAGE,
        ADMIN_USERNAME=cfg.ADMIN_USERNAME,
        ADMIN_PASSWORD=cfg.ADMIN_PASSWORD,
    )
    if config_overrides:
        app.config.update(config_overrides)

    from database import init_db, init_schema
    init_db(app)
    init_schema(app.config["DATABASE"])

    from auth import bp as auth_bp, register_auth_extensions
    from errors import register_error_handlers
    register_auth_extensions(app)
    register_error_handlers(app)
    app.register_blueprint(auth_bp)

    from blueprints.public import bp as public_bp
    from blueprints.comments import bp as comments_bp
    from blueprints.admin import bp as admin_bp
    from blueprints.api import bp as api_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app