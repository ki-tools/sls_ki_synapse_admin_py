from flask import current_app as app, make_response
from flask import redirect, url_for, request, render_template
from flask_login import login_required
from www.services import AuthService
from www.core import AuthEmailNotVerifiedError, AuthForbiddenError, AuthLoginFailureError, Cookies


@app.route("/login")
def login():
    request_uri = AuthService.get_redirect_uri(request.base_url)
    response = make_response(redirect(request_uri))
    Cookies.user_email_delete(response)
    return response


@app.route("/login/callback")
def login_callback():
    code = request.args.get("code")
    request_url = request.url
    request_base_url = request.base_url
    try:
        user = AuthService.handle_callback_and_login(code, request_url, request_base_url)
        response = make_response(redirect(request.args.get("next") or url_for("home")))
        Cookies.user_email_set(response, user.email)
        return response
    except AuthEmailNotVerifiedError:
        return "Email not verified by Google.", 400
    except (AuthForbiddenError, AuthLoginFailureError):
        return redirect(url_for('login_forbidden'))


@app.route("/logout")
@login_required
def logout():
    AuthService.logout_user()
    response = make_response(redirect(url_for('home')))
    Cookies.user_email_delete(response)
    return response


@app.route("/login/forbidden")
def login_forbidden():
    return render_template('login/forbidden.html')
