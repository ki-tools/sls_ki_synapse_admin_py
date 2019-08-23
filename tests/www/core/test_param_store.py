import pytest
import os
from moto import mock_ssm
from www.core import ParamStore


@pytest.fixture
def key():
    return 'TEST_KEY'


@pytest.fixture
def value():
    return 'TEST_VALUE'


@mock_ssm
def test_get(key, value, monkeypatch):
    # TODO: also test 'only_from_env' param
    assert os.environ.get(key) is None
    assert ParamStore._get_from_os(key) is None
    assert ParamStore._get_from_ssm(key) is None
    assert ParamStore.get(key) is None

    # From OS
    monkeypatch.setenv(key, value)
    assert os.environ.get(key) == value
    assert ParamStore.get(key) == value

    monkeypatch.delenv(key, raising=False)
    assert os.environ.get(key) is None
    assert ParamStore.get(key) is None

    # From SSM
    ParamStore._set_ssm_parameter(key, value)
    assert ParamStore.get(key) == value


@mock_ssm
def test_get_bool(key, monkeypatch):
    # TODO: also test 'only_from_env' param
    true_values = ['True', 'tRuE', 'TRUE', 'true']
    false_values = ['False', 'fAlSe', 'FALSE', 'false', None, '']

    # From OS
    for true_value in true_values:
        monkeypatch.delenv(key, raising=False)
        ParamStore._delete_ssm_parameter(key)
        assert os.environ.get(key) is None
        assert ParamStore._get_from_os(key) is None
        assert ParamStore._get_from_ssm(key) is None
        assert ParamStore.get_bool(key) is False

        monkeypatch.setenv(key, true_value)
        assert os.environ.get(key) == true_value
        assert ParamStore.get_bool(key) is True

        monkeypatch.delenv(key, raising=False)
        assert os.environ.get(key) is None
        assert ParamStore.get_bool(key) is False

        # From SSM
        ParamStore._set_ssm_parameter(key, true_value)
        assert ParamStore.get_bool(key) is True

    for false_value in false_values:
        monkeypatch.delenv(key, raising=False)
        ParamStore._delete_ssm_parameter(key)
        assert os.environ.get(key) is None
        assert ParamStore._get_from_os(key) is None
        assert ParamStore._get_from_ssm(key) is None
        assert ParamStore.get_bool(key) is False

        if false_value is None:
            monkeypatch.delenv(key, raising=False)
            assert os.environ.get(key) is None
        else:
            monkeypatch.setenv(key, false_value)
            assert os.environ.get(key) == str(false_value)
        assert ParamStore.get_bool(key) is False

        monkeypatch.delenv(key, raising=False)
        assert os.environ.get(key) is None
        assert ParamStore.get_bool(key) is False

        # From SSM
        ParamStore._set_ssm_parameter(key, str(false_value))
        assert ParamStore.get_bool(key) is False


@mock_ssm
def test_get_int(key, monkeypatch):
    # TODO: also test 'only_from_env' param
    assert os.environ.get(key) is None
    assert ParamStore._get_from_os(key) is None
    assert ParamStore._get_from_ssm(key) is None
    assert ParamStore.get(key) is None

    value = "123"
    expected_int = 123

    # From OS
    monkeypatch.setenv(key, value)
    assert os.environ.get(key) == value
    assert ParamStore.get_int(key) == expected_int

    monkeypatch.delenv(key, raising=False)
    assert os.environ.get(key) is None
    assert ParamStore.get(key) is None

    # From SSM
    ParamStore._set_ssm_parameter(key, value)
    assert ParamStore.get_int(key) == expected_int

    # Returns None
    ParamStore._set_ssm_parameter(key, '')
    assert ParamStore.get_int(key) is None

    ParamStore._delete_ssm_parameter(key)
    assert ParamStore.get(key) is None
    assert ParamStore.get_int(key) is None

    # Returns default
    assert ParamStore.get_int(key, default=321) == 321


@mock_ssm
def test_get_list(key, monkeypatch):
    # TODO: also test 'only_from_env' param
    value = ' a , b,c ,1  , 2, 3,,  ,   ,'
    expected_list = ['a', 'b', 'c', '1', '2', '3']

    # From OS
    monkeypatch.setenv(key, value)
    assert ParamStore.get_list(key) == expected_list

    monkeypatch.delenv(key, raising=False)
    assert os.environ.get(key) is None

    # From SSM
    ParamStore._set_ssm_parameter(key, value)
    assert ParamStore.get_list(key) == expected_list


@mock_ssm
def test__get_from_os(key, value, monkeypatch):
    assert os.environ.get(key) is None
    assert ParamStore._get_from_os(key) is None
    assert ParamStore._get_from_ssm(key) is None
    assert ParamStore.get(key) is None

    monkeypatch.setenv(key, value)
    assert os.environ.get(key) == value
    assert ParamStore._get_from_os(key) == value


@mock_ssm
def test__get_from_ssm(key, value):
    assert os.environ.get(key) is None
    assert ParamStore._get_from_os(key) is None
    assert ParamStore._get_from_ssm(key) is None
    assert ParamStore.get(key) is None

    ParamStore._set_ssm_parameter(key, value)
    assert ParamStore._get_from_ssm(key) == value


@mock_ssm
def test__set_ssm_parameter(key, value):
    assert os.environ.get(key) is None
    assert ParamStore._get_from_ssm(key) is None

    ParamStore._set_ssm_parameter(key, value)
    assert ParamStore._get_from_ssm(key) == value


@mock_ssm
def test__delete_ssm_parameter(key, value):
    assert os.environ.get(key) is None
    assert ParamStore._get_from_ssm(key) is None

    ParamStore._set_ssm_parameter(key, value)
    assert ParamStore._get_from_ssm(key) == value

    assert ParamStore._delete_ssm_parameter(key) is True
    assert ParamStore._get_from_ssm(key) is None


def test__build_ssm_key(monkeypatch):
    monkeypatch.setenv('SERVICE_NAME', 'a')
    monkeypatch.setenv('SERVICE_STAGE', 'b')
    assert ParamStore._build_ssm_key('c') == '/a/b/c'
