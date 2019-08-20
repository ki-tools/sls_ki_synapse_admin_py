import pytest
from www.core import ParamStore
from www.services import EncryptSynapseSpaceService


def test_it_sets_the_project_id(fake_synapse_id):
    service = EncryptSynapseSpaceService(fake_synapse_id)
    assert service.project_id == fake_synapse_id


def test_execute(syn_test_helper):
    project = syn_test_helper.create_project()
    service = EncryptSynapseSpaceService(project_id=project.id)

    before, _ = service._get_project_storage_setting()
    # A new project will not have any storage location setting.
    # Storage location settings are only available once they have been changed from the default.
    assert before is None

    errors = service.execute()
    assert len(errors) == 0
    after, _ = service._get_project_storage_setting()
    assert after is not None
    assert after != before
    assert ParamStore.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID() in after.get('locations')


def test_execute_errors(syn_client, fake_synapse_id, mocker):
    with mocker.mock_module.patch.object(syn_client, 'setStorageLocation') as mock:
        mock.side_effect = Exception('Random Error...')
        errors = EncryptSynapseSpaceService(fake_synapse_id).execute()
        assert len(errors) == 1
        assert errors[0] == 'Unknown error setting storage location.'


def test_validate(syn_test_helper):
    target_project = syn_test_helper.create_project()
    service = EncryptSynapseSpaceService(project_id=target_project.id)
    project, error = service.validate()
    assert error is None
    assert project is not None
    assert project.id == target_project.id


def test_validate_project_errors(fake_synapse_id):
    service = EncryptSynapseSpaceService(project_id=fake_synapse_id)
    project, error = service.validate()
    assert project is None
    assert error == 'Synapse project ID: {0} does not exist.'.format(fake_synapse_id)


def test_validate_storage_setting_errors():
    # TODO: Test this.
    pass
