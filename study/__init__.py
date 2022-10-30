from flask import Flask, url_for, redirect
import os

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite')
    )

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/")
    @app.route("/index")
    def index():
        return redirect(url_for("decks.see_user"))

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from .blueprints import decks
    app.register_blueprint(decks.main.bp)

    from .blueprints import classes
    app.register_blueprint(classes.main.bp)

    from .blueprints import routines
    app.register_blueprint(routines.main.bp)

    from .learn import learn
    app.register_blueprint(learn.bp)

    from . import statistics
    app.register_blueprint(statistics.bp)

    from .blueprints import spaced_repetition
    app.register_blueprint(spaced_repetition.main.bp)

    return app