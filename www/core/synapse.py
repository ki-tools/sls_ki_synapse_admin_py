from . import Env
import os
import tempfile
from datetime import datetime
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

    TEAM_MANAGER_PERMS = [
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

    TABLE_COL_CACHE = {}

    @classmethod
    def build_syn_table_row(cls, syn_table_id, row_data):
        """Builds an array of row values for a Synapse Table.

        Args:
            syn_table_id: The ID of the Synapse table to add a row to.
            row_data: Dictionary of field names and values.

        Returns:
            Array
        """
        if syn_table_id not in cls.TABLE_COL_CACHE:
            cls.TABLE_COL_CACHE[syn_table_id] = [c['name'] for c in
                                                 list(Synapse.client().getTableColumns(syn_table_id))]

        table_columns = cls.TABLE_COL_CACHE[syn_table_id]

        # Make sure the specified fields exist in the table.
        for column in row_data:
            if column not in table_columns:
                raise Exception('Column: {0} does not exist in table: {1}'.format(column, syn_table_id))

        # Build the row data.
        new_row = []

        for column in table_columns:
            if column in row_data:
                new_row.append(row_data[column])
            else:
                new_row.append(None)

        return new_row

    @classmethod
    def date_to_synapse_date_timestamp(cls, date):
        """Converts a Date into a timestamp suitable for a DATE field in a Synapse table.

        Args:
            date: The date to convert.

        Returns:
            Integer.
        """
        if date:
            return int(datetime(date.year, date.month, date.day).timestamp()) * 1000
        else:
            return None
