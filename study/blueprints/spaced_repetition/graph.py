from flask import render_template

from .main import bp

@bp.route("/graph")
def graph():
    return render_template("spaced_repetition/graph.html")