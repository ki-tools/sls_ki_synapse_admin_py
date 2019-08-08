from flask_login import LoginManager
from oauthlib.oauth2 import WebApplicationClient
from flask import Flask
from www.models import User

# Load the config
import www.config

# Import ParamStore after the config is loaded.
from www.core import ParamStore

# Flask app setup.
app = Flask(__name__)

# User session management setup.
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.session_protection = "strong"

# OAuth 2 client setup.
auth_client = WebApplicationClient(ParamStore.GOOGLE_CLIENT_ID())


def init_all():
    if ParamStore.FLASK_LOGIN_DISABLED() and ParamStore.FLASK_ENV() != 'test':
        raise Exception('Only the "test" environment can have FLASK_LOGIN_DISABLED set to True')

    login_manager.init_app(app)


with app.app_context():
    app.secret_key = ParamStore.SECRET_KEY()
    app.testing = ParamStore.FLASK_TESTING()
    app.config['LOGIN_DISABLED'] = ParamStore.FLASK_LOGIN_DISABLED()
    app.debug = ParamStore.FLASK_DEBUG()

    init_all()

    # Load the views AFTER the app has been instantiated.
    import www.views


# Flask-Login helper to retrieve a User object.
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
