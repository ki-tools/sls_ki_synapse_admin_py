import pytest
from www.core import Env


def test__get_principal_permissions_var(monkeypatch):
    var_name = 'PRINCIPAL_PERMISSION_VAR'

    monkeypatch.setenv(var_name, '10:ADMIN,11:CAN_EDIT_AND_DELETE,12:CAN_EDIT,13:CAN_DOWNLOAD,14:CAN_VIEW')
    expected = [
        {'id': 10, 'permission': 'ADMIN'},
        {'id': 11, 'permission': 'CAN_EDIT_AND_DELETE'},
        {'id': 12, 'permission': 'CAN_EDIT'},
        {'id': 13, 'permission': 'CAN_DOWNLOAD'},
        {'id': 14, 'permission': 'CAN_VIEW'}
    ]

    value = Env._get_principal_permissions_var(var_name)
    assert value == expected

    monkeypatch.setenv(var_name, '')
    value = Env._get_principal_permissions_var(var_name)
    assert value == []

    with pytest.raises(Exception) as ex:
        monkeypatch.setenv(var_name, '1:PERM:A,2')
        Env._get_principal_permissions_var(var_name)
    assert 'Invalid format for PRINCIPAL_PERMISSION_VAR:' in str(ex.value)

    with pytest.raises(Exception) as ex:
        monkeypatch.setenv(var_name, 'a:PERM,1:PERM')
        Env._get_principal_permissions_var(var_name)
    assert 'invalid literal for int()' in str(ex.value)
