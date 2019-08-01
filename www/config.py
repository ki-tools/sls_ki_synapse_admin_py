import os
import json
from www.core import ParamStore

# Try and load environment variables from the private ENV settings file (if available).
# This file should only be present during local development
if ParamStore.FLASK_ENV() in ['development', 'test']:
    module_dir = os.path.dirname(os.path.abspath(__file__))

    env_file = os.path.join(module_dir, '../private.env.json')

    if os.path.isfile(env_file):
        with open(env_file) as f:
            config = json.load(f).get(ParamStore.FLASK_ENV())

            for key, value in config.items():
                os.environ[key] = value
