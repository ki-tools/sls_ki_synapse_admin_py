from flask import current_app as app
from flask import redirect, url_for, request, render_template
from flask_login import login_required, login_user, logout_user
import requests
import json
from www import server
from www.core import ParamStore
from www.models import User


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = _get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = server.auth_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def auth_callback():
    # Get authorization code Google sent back.
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user.
    google_provider_cfg = _get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens.
    token_url, headers, body = server.auth_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(ParamStore.GOOGLE_CLIENT_ID(), ParamStore.GOOGLE_CLIENT_SECRET()),
    )

    # Parse the tokens
    server.auth_client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email.
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = server.auth_client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Make sure the email is verified.
    # The user authenticated with Google, authorized the app,
    # and now we've verified their email through Google.
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]

        if _can_login(users_email):
            login_user(User(unique_id, users_email))
            # Send user back to homepage or the 'next' location.
            return redirect(request.args.get("next") or url_for("home"))
        else:
            return redirect(url_for('forbidden'))
    else:
        return "User email not available or not verified by Google.", 400


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/forbidden")
def forbidden():
    return render_template('auth/forbidden.html')


def _get_google_provider_cfg():
    return requests.get(ParamStore.GOOGLE_DISCOVERY_URL()).json()


def _can_login(email):
    whitelist = ParamStore.LOGIN_WHITELIST()
    allowed_emails = [e.strip() for e in whitelist.split(',') if e and e.strip()]
    return email in allowed_emails
