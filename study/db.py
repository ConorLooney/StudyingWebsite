import sqlite3
import click
from flask import (
    current_app, g, app
)

def init_db():
    db = sqlite3.connect(
            current_app.config["DATABASE"]
        )
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))

@click.command("init-db")
def init_db_command():
    init_db()
    print("Database made")

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()

def get_db():
    if "db" not in g:
        db = sqlite3.connect(
            current_app.config["DATABASE"]
        )
        db.row_factory = sqlite3.Row
        g.db = db
    return g.db

def to_bool(bit):
    return str(bit) == "1"