from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_FOLDER='uploads',
        TEMPLATES_AUTO_RELOAD=True
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app