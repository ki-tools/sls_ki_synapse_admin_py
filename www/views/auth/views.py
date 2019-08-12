from flask import current_app as app
from flask import redirect, url_for, request, render_template
from flask_login import login_required
from www.services import AuthService
from www.core import AuthEmailNotVerified, AuthForbidden


@app.route("/login")
def login():
    request_uri = AuthService.get_redirect_uri(request.base_url)
    return redirect(request_uri)


@app.route("/login/callback")
def auth_callback():
    code = request.args.get("code")
    request_url = request.url
    request_base_url = request.base_url
    try:
        AuthService.handle_callback_and_login(code, request_url, request_base_url)
        return redirect(request.args.get("next") or url_for("home"))
    except AuthEmailNotVerified:
        return "Email not verified by Google.", 400
    except AuthForbidden:
        return redirect(url_for('forbidden'))


@app.route("/logout")
@login_required
def logout():
    AuthService.logout_user()
    return redirect(url_for('home'))


@app.route("/forbidden")
def forbidden():
    return render_template('auth/forbidden.html')
