import pytest
from www.core import Env, Synapse
from datetime import date


def test_client():
    assert Synapse.client() is not None
    profile = Synapse.client().getUserProfile(refresh=True)
    assert profile['userName'] == Env.SYNAPSE_USERNAME()


def test_get_perms_by_code():
    for code in Synapse.ALL_PERM_CODES:
        perms = Synapse.get_perms_by_code(code)
        if code == 'ADMIN':
            assert perms == Synapse.ADMIN_PERMS
        elif code == 'CAN_EDIT_AND_DELETE':
            assert perms == Synapse.CAN_EDIT_AND_DELETE_PERMS
        elif code == 'CAN_EDIT':
            assert perms == Synapse.CAN_EDIT_PERMS
        elif code == 'CAN_DOWNLOAD':
            assert perms == Synapse.CAN_DOWNLOAD_PERMS
        elif code == 'CAN_VIEW':
            assert perms == Synapse.CAN_VIEW_PERMS
        else:
            raise Exception('Unexpected perms: {0} for code: {1}'.format(perms, code))


def test_date_to_synapse_date_timestamp():
    d = date(year=2020, month=1, day=1)
    ts = Synapse.date_to_synapse_date_timestamp(d)
    assert date.fromtimestamp(ts / 1000) == d
