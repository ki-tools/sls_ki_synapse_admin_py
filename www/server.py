from www.core import ParamStore
from flask import Flask

app = Flask(__name__)
app.secret_key = ParamStore.SECRET_KEY(default='default-secret-key')

# Load the views.
import www.views
