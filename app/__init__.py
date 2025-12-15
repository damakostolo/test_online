from flask import Flask, render_template
from flask_login import current_user
from .config import Config
from .extensions import db, migrate, login_manager, bcrypt, csrf
from .auth.routes import auth_bp
from .tests.routes import tests_bp
from .results.routes import results_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tests_bp)
    app.register_blueprint(results_bp)

    @app.context_processor
    def inject_user():
        return {"current_user": current_user}

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
