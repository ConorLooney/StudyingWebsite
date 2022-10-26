from flask import Flask
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

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import decks
    app.register_blueprint(decks.bp)
    app.add_url_rule("/", endpoint="/index")

    from . import routines
    app.register_blueprint(routines.bp)

    from .learn import learn
    app.register_blueprint(learn.bp)

    from . import classes
    app.register_blueprint(classes.bp)

    from . import statistics
    app.register_blueprint(statistics.bp)

    from . import spaced_rep
    app.register_blueprint(spaced_rep.bp)

    return app