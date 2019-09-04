from flask_login import LoginManager
from oauthlib.oauth2 import WebApplicationClient
from flask import Flask
from www.models import User
import www.config as config
from www.core import Env

# Load the config if running an applicable environment.
config.load_local_if_applicable()

# Flask app setup.
app = Flask(__name__)

# User session management setup.
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.session_protection = "strong"

# OAuth 2 client setup.
auth_client = WebApplicationClient(Env.GOOGLE_CLIENT_ID())


def init_all():
    if Env.FLASK_LOGIN_DISABLED() and Env.FLASK_ENV() != config.Envs.TEST:
        raise Exception('Only the "{0}" environment can have FLASK_LOGIN_DISABLED set to True'.format(config.Envs.TEST))

    login_manager.init_app(app)


with app.app_context():
    app.secret_key = Env.SECRET_KEY()
    app.testing = Env.FLASK_TESTING()
    app.config['LOGIN_DISABLED'] = Env.FLASK_LOGIN_DISABLED()
    app.debug = Env.FLASK_DEBUG()

    init_all()

    # Load the views AFTER the app has been instantiated.
    import www.views


# Flask-Login helper to retrieve a User object.
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
