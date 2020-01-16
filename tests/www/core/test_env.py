import pytest
import json
from www.core import Env


def test__get_principal_permissions_var(monkeypatch):
    var_name = 'PRINCIPAL_PERMISSION_VAR'

    # Integers
    monkeypatch.setenv(var_name, '10:ADMIN,11:CAN_EDIT_AND_DELETE,12:CAN_EDIT,13:CAN_DOWNLOAD,14:CAN_VIEW')
    expected = [
        {'id': 10, 'permission': 'ADMIN'},
        {'id': 11, 'permission': 'CAN_EDIT_AND_DELETE'},
        {'id': 12, 'permission': 'CAN_EDIT'},
        {'id': 13, 'permission': 'CAN_DOWNLOAD'},
        {'id': 14, 'permission': 'CAN_VIEW'}
    ]

    value = Env._get_id_permissions_var(var_name, int)
    assert value == expected

    monkeypatch.setenv(var_name, '')
    value = Env._get_id_permissions_var(var_name, int)
    assert value == []

    with pytest.raises(Exception) as ex:
        monkeypatch.setenv(var_name, '1:PERM:A,2')
        Env._get_id_permissions_var(var_name, int)
    assert 'Invalid format for PRINCIPAL_PERMISSION_VAR:' in str(ex.value)

    with pytest.raises(Exception) as ex:
        monkeypatch.setenv(var_name, 'a:PERM,1:PERM')
        Env._get_id_permissions_var(var_name, int)
    assert 'invalid literal for int()' in str(ex.value)

    # Strings
    monkeypatch.setenv(var_name,
                       'syn10:ADMIN,syn11:CAN_EDIT_AND_DELETE,syn12:CAN_EDIT,syn13:CAN_DOWNLOAD,syn14:CAN_VIEW')
    expected = [
        {'id': 'syn10', 'permission': 'ADMIN'},
        {'id': 'syn11', 'permission': 'CAN_EDIT_AND_DELETE'},
        {'id': 'syn12', 'permission': 'CAN_EDIT'},
        {'id': 'syn13', 'permission': 'CAN_DOWNLOAD'},
        {'id': 'syn14', 'permission': 'CAN_VIEW'}
    ]

    value = Env._get_id_permissions_var(var_name, str)
    assert value == expected

    monkeypatch.setenv(var_name, '')
    value = Env._get_id_permissions_var(var_name, str)
    assert value == []

    with pytest.raises(Exception) as ex:
        monkeypatch.setenv(var_name, '1:PERM:A,2')
        Env._get_id_permissions_var(var_name, str)
    assert 'Invalid format for PRINCIPAL_PERMISSION_VAR:' in str(ex.value)
