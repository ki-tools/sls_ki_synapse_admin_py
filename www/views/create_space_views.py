from flask import render_template
from server import app


@app.route("/create-space")
def create_space():
    return render_template("create_space.html")
