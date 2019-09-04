from sls_tools.param_store import ParamStore
import uuid


class Env:
    @staticmethod
    def FLASK_ENV(default='development'):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get('FLASK_ENV', default=default, store=ParamStore.Stores.OS).value

    @staticmethod
    def FLASK_DEBUG(default=False):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get('FLASK_DEBUG', default=default, store=ParamStore.Stores.OS).to_bool()

    @staticmethod
    def FLASK_TESTING(default=False):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get('FLASK_TESTING', default=default, store=ParamStore.Stores.OS).to_bool()

    @staticmethod
    def FLASK_LOGIN_DISABLED(default=False):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get('FLASK_LOGIN_DISABLED', default=default, store=ParamStore.Stores.OS).to_bool()

    @staticmethod
    def SERVICE_NAME(default=None):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get('SERVICE_NAME', default=default, store=ParamStore.Stores.OS).value

    @staticmethod
    def SERVICE_STAGE(default=None):
        """
        This variable must be set on the OS (not on SSM)
        """
        return ParamStore.get('SERVICE_STAGE', default=default, store=ParamStore.Stores.OS).value

    @staticmethod
    def SECRET_KEY(default=str(uuid.uuid4())):
        return ParamStore.get('SECRET_KEY', default).value

    @staticmethod
    def LOG_LEVEL(default=None):
        return ParamStore.get('LOG_LEVEL', default).value

    @staticmethod
    def SYNAPSE_USERNAME(default=None):
        return ParamStore.get('SYNAPSE_USERNAME', default).value

    @staticmethod
    def SYNAPSE_PASSWORD(default=None):
        return ParamStore.get('SYNAPSE_PASSWORD', default).value

    @staticmethod
    def SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID(default=None):
        return ParamStore.get('SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID', default).to_int()

    @staticmethod
    def GOOGLE_CLIENT_ID(default=None):
        return ParamStore.get('GOOGLE_CLIENT_ID', default).value

    @staticmethod
    def GOOGLE_CLIENT_SECRET(default=None):
        return ParamStore.get('GOOGLE_CLIENT_SECRET', default).value

    @staticmethod
    def GOOGLE_DISCOVERY_URL(default='https://accounts.google.com/.well-known/openid-configuration'):
        return ParamStore.get('GOOGLE_DISCOVERY_URL', default).value

    @staticmethod
    def LOGIN_WHITELIST(default=[]):
        return ParamStore.get('LOGIN_WHITELIST', default).to_list(delimiter=',')

    @staticmethod
    def CREATE_SYNAPSE_SPACE_ADMIN_TEAM_IDS(default=[]):
        return ParamStore.get('CREATE_SYNAPSE_SPACE_ADMIN_TEAM_IDS', default).to_list(delimiter=',')

    @staticmethod
    def CREATE_SYNAPSE_SPACE_DEFAULT_WIKI_PROJECT_ID(default=None):
        return ParamStore.get('CREATE_SYNAPSE_SPACE_DEFAULT_WIKI_PROJECT_ID', default).value
