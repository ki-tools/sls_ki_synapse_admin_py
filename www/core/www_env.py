from www.core import ParamStore
import uuid


class WWWEnv:
    @staticmethod
    def FLASK_ENV(default='development'):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get('FLASK_ENV', default=default, only_from_env=True)

    @staticmethod
    def FLASK_DEBUG(default=False):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get_bool('FLASK_DEBUG', default=default, only_from_env=True)

    @staticmethod
    def FLASK_TESTING(default=False):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get_bool('FLASK_TESTING', default=default, only_from_env=True)

    @staticmethod
    def FLASK_LOGIN_DISABLED(default=False):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get_bool('FLASK_LOGIN_DISABLED', default=default, only_from_env=True)

    @staticmethod
    def SERVICE_NAME(default=None):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get('SERVICE_NAME', default=default, only_from_env=True)

    @staticmethod
    def SERVICE_STAGE(default=None):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get('SERVICE_STAGE', default=default, only_from_env=True)

    @staticmethod
    def SECRET_KEY(default=str(uuid.uuid4())):
        return ParamStore.get('SECRET_KEY', default)

    @staticmethod
    def LOG_LEVEL(default=None):
        return ParamStore.get('LOG_LEVEL', default)

    @staticmethod
    def SYNAPSE_USERNAME(default=None):
        return ParamStore.get('SYNAPSE_USERNAME', default)

    @staticmethod
    def SYNAPSE_PASSWORD(default=None):
        return ParamStore.get('SYNAPSE_PASSWORD', default)

    @staticmethod
    def SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID(default=None):
        return ParamStore.get_int('SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID', default)

    @staticmethod
    def GOOGLE_CLIENT_ID(default=None):
        return ParamStore.get('GOOGLE_CLIENT_ID', default)

    @staticmethod
    def GOOGLE_CLIENT_SECRET(default=None):
        return ParamStore.get('GOOGLE_CLIENT_SECRET', default)

    @staticmethod
    def GOOGLE_DISCOVERY_URL(default='https://accounts.google.com/.well-known/openid-configuration'):
        return ParamStore.get('GOOGLE_DISCOVERY_URL', default)

    @staticmethod
    def LOGIN_WHITELIST(default=[]):
        return ParamStore.get_list('LOGIN_WHITELIST', default, delimiter=',')

    @staticmethod
    def CREATE_SYNAPSE_SPACE_ADMIN_TEAM_IDS(default=[]):
        return ParamStore.get_list('CREATE_SYNAPSE_SPACE_ADMIN_TEAM_IDS', default, delimiter=',')

    @staticmethod
    def CREATE_SYNAPSE_SPACE_DEFAULT_WIKI_PROJECT_ID(default=None):
        return ParamStore.get('CREATE_SYNAPSE_SPACE_DEFAULT_WIKI_PROJECT_ID', default)
