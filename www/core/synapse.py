from . import Env
import os
import tempfile
import synapseclient


class Synapse:
    _synapse_client = None

    ALL_PERM_CODES = ['ADMIN', 'CAN_EDIT_AND_DELETE', 'CAN_EDIT', 'CAN_DOWNLOAD', 'CAN_VIEW']

    ADMIN_PERMS = [
        'UPDATE',
        'DELETE',
        'CHANGE_PERMISSIONS',
        'CHANGE_SETTINGS',
        'CREATE',
        'DOWNLOAD',
        'READ',
        'MODERATE'
    ]

    CAN_EDIT_AND_DELETE_PERMS = [
        'DOWNLOAD',
        'UPDATE',
        'CREATE',
        'DELETE',
        'READ'
    ]

    CAN_EDIT_PERMS = [
        'DOWNLOAD',
        'UPDATE',
        'CREATE',
        'READ'
    ]

    CAN_DOWNLOAD_PERMS = [
        'DOWNLOAD',
        'READ'
    ]

    CAN_VIEW_PERMS = [
        'READ'
    ]

    TEAM_MANAGER_PERMISSIONS = [
        'SEND_MESSAGE',
        'READ',
        'UPDATE',
        'TEAM_MEMBERSHIP_UPDATE',
        'DELETE'
    ]

    @classmethod
    def get_perms_by_code(cls, code):
        code = code.upper() if code else None
        if code not in cls.ALL_PERM_CODES:
            raise Exception('Invalid permissions code: {0}'.format(code))
        return getattr(cls, '{0}_PERMS'.format(code))

    @classmethod
    def client(cls):
        """Gets a logged in instance of the synapseclient."""
        if not cls._synapse_client:
            # Lambda can only write to /tmp so update the CACHE_ROOT_DIR.
            synapseclient.cache.CACHE_ROOT_DIR = os.path.join(tempfile.gettempdir(), 'synapseCache')

            # Multiprocessing is not supported on Lambda.
            synapseclient.config.single_threaded = True

            syn_user = Env.SYNAPSE_USERNAME()
            syn_pass = Env.SYNAPSE_PASSWORD()
            cls._synapse_client = synapseclient.Synapse(skip_checks=True)
            cls._synapse_client.login(syn_user, syn_pass, silent=True)

        return cls._synapse_client
