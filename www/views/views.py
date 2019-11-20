from flask import current_app as app, request, render_template
from ..core import Cookies


@app.route("/")
def home():
    return render_template("home.html", user=Cookies.user_email_get(request))
