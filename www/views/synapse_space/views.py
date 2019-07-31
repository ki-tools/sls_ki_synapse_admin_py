from flask import render_template
from server import app


@app.route("/synapse_space/create")
def create_synapse_space():
    return render_template("synapse_space/create.html")
