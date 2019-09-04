import pytest
from www.core import Env
from www.services import EncryptSynapseSpaceService


def test_it_sets_the_project_id(fake_synapse_id):
    service = EncryptSynapseSpaceService(fake_synapse_id)
    assert service.project_id == fake_synapse_id


def test_execute(syn_test_helper):
    project = syn_test_helper.create_project()
    service = EncryptSynapseSpaceService(project_id=project.id)

    before, _ = EncryptSynapseSpaceService.Validations._get_project_storage_setting(project.id)
    # A new project will not have any storage location setting.
    # Storage location settings are only available once they have been changed from the default.
    assert before is None

    assert service.execute() == service
    assert len(service.errors) == 0
    after, _ = EncryptSynapseSpaceService.Validations._get_project_storage_setting(project.id)
    assert after is not None
    assert after != before
    assert Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID() in after.get('locations')


def test_execute_errors(syn_client, fake_synapse_id, mocker):
    with mocker.mock_module.patch.object(syn_client, 'setStorageLocation') as mock:
        mock.side_effect = Exception('Random Error...')
        errors = EncryptSynapseSpaceService(fake_synapse_id).execute().errors
        assert len(errors) == 1
        assert 'Error setting storage location:' in errors[0]


###############################################################################
# Validations
###############################################################################

def test_validate(syn_test_helper):
    target_project = syn_test_helper.create_project()
    project, error = EncryptSynapseSpaceService.Validations.validate(target_project.id)
    assert error is None
    assert project is not None
    assert project.id == target_project.id


def test_validate_project_errors(fake_synapse_id):
    project, error = EncryptSynapseSpaceService.Validations.validate(fake_synapse_id)
    assert project is None
    assert error == 'Synapse project ID: {0} does not exist.'.format(fake_synapse_id)


def test_validate_storage_setting_errors():
    # TODO: Test this.
    pass
